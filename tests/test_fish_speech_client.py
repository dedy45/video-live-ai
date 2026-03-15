"""Tests for Fish-Speech API client adapter."""

from __future__ import annotations

import json
import os
import pytest

os.environ["MOCK_MODE"] = "true"


# === FishSpeechClient Unit Tests ===


@pytest.mark.asyncio
async def test_synthesize_posts_v1_tts_with_reference_payload(httpx_mock) -> None:
    """Client should POST msgpack to /v1/tts with raw reference audio bytes."""
    import httpx
    import msgpack
    from src.voice.fish_speech_client import FishSpeechClient

    captured: dict[str, object] = {}

    def handle_request(request: httpx.Request) -> httpx.Response:
        captured["content_type"] = request.headers.get("content-type")
        captured["payload"] = msgpack.unpackb(request.content, raw=False)
        return httpx.Response(200, content=b"WAVDATA")

    httpx_mock.add_callback(
        handle_request,
        method="POST",
        url="http://127.0.0.1:8080/v1/tts",
    )
    client = FishSpeechClient(base_url="http://127.0.0.1:8080", timeout_ms=3000)
    audio = await client.synthesize(
        text="halo kak",
        reference_audio_b64="eHh4",
        reference_text="halo",
    )
    assert audio == b"WAVDATA"
    assert captured["content_type"] == "application/msgpack"
    assert captured["payload"] == {
        "text": "halo kak",
        "references": [
            {"audio": b"xxx", "text": "halo"},
        ],
    }


@pytest.mark.asyncio
async def test_synthesize_raises_on_non_200(httpx_mock) -> None:
    """Client should raise FishSpeechClientError on non-200 response."""
    from src.voice.fish_speech_client import FishSpeechClient, FishSpeechClientError

    httpx_mock.add_response(
        method="POST",
        url="http://127.0.0.1:8080/v1/tts",
        status_code=500,
        text="Internal Server Error",
    )
    client = FishSpeechClient(base_url="http://127.0.0.1:8080", timeout_ms=3000)
    with pytest.raises(FishSpeechClientError, match="500"):
        await client.synthesize(text="halo kak")


@pytest.mark.asyncio
async def test_synthesize_raises_on_timeout(httpx_mock) -> None:
    """Client should raise FishSpeechClientError on timeout."""
    import httpx as _httpx
    from src.voice.fish_speech_client import FishSpeechClient, FishSpeechClientError

    httpx_mock.add_exception(
        _httpx.TimeoutException("timed out"),
        url="http://127.0.0.1:8080/v1/tts",
    )
    client = FishSpeechClient(base_url="http://127.0.0.1:8080", timeout_ms=100)
    with pytest.raises(FishSpeechClientError, match="timed out"):
        await client.synthesize(text="halo kak")


@pytest.mark.asyncio
async def test_synthesize_raises_on_connection_error(httpx_mock) -> None:
    """Client should raise FishSpeechClientError when server is unreachable."""
    import httpx as _httpx
    from src.voice.fish_speech_client import FishSpeechClient, FishSpeechClientError

    httpx_mock.add_exception(
        _httpx.ConnectError("Connection refused"),
        url="http://127.0.0.1:8080/v1/tts",
    )
    client = FishSpeechClient(base_url="http://127.0.0.1:8080", timeout_ms=3000)
    with pytest.raises(FishSpeechClientError, match="unreachable"):
        await client.synthesize(text="halo kak")


@pytest.mark.asyncio
async def test_health_check_returns_true_on_reachable(httpx_mock) -> None:
    """Health check should return dict with reachable=True when server responds."""
    from src.voice.fish_speech_client import FishSpeechClient

    httpx_mock.add_response(
        method="GET",
        url="http://127.0.0.1:8080/v1/health",
        status_code=200,
        json={"status": "ok"},
    )
    client = FishSpeechClient(base_url="http://127.0.0.1:8080", timeout_ms=3000)
    result = await client.health_check()
    assert isinstance(result, dict)
    assert result["reachable"] is True


@pytest.mark.asyncio
async def test_health_check_accepts_kui_json_openapi_endpoint(httpx_mock) -> None:
    """Health check should accept the Kui OpenAPI JSON endpoint used by Fish-Speech v1.5."""
    from src.voice.fish_speech_client import FishSpeechClient

    httpx_mock.add_response(
        method="GET",
        url="http://127.0.0.1:8080/v1/health",
        status_code=405,
        text="method not allowed",
    )
    httpx_mock.add_response(
        method="GET",
        url="http://127.0.0.1:8080/health",
        status_code=404,
        text="not found",
    )
    httpx_mock.add_response(
        method="GET",
        url="http://127.0.0.1:8080/v1/models",
        status_code=404,
        text="not found",
    )
    httpx_mock.add_response(
        method="GET",
        url="http://127.0.0.1:8080/json",
        status_code=200,
        json={"openapi": "3.1.0", "info": {"title": "Fish Speech API", "version": "1.5.0"}},
    )

    client = FishSpeechClient(base_url="http://127.0.0.1:8080", timeout_ms=3000)
    result = await client.health_check()
    assert isinstance(result, dict)
    assert result["reachable"] is True
    assert result["endpoint"] == "/json"


@pytest.mark.asyncio
async def test_health_check_returns_false_on_unreachable(httpx_mock) -> None:
    """Health check should return dict with reachable=False when server is unreachable."""
    import httpx as _httpx
    from src.voice.fish_speech_client import FishSpeechClient

    # Add exceptions for all health endpoints the client tries
    for path in ("/v1/health", "/health", "/v1/models", "/json"):
        httpx_mock.add_exception(
            _httpx.ConnectError("Connection refused"),
            url=f"http://127.0.0.1:9999{path}",
        )
    client = FishSpeechClient(base_url="http://127.0.0.1:9999", timeout_ms=1000)
    result = await client.health_check()
    assert isinstance(result, dict)
    assert result["reachable"] is False


@pytest.mark.asyncio
async def test_health_check_returns_false_on_not_found_endpoints(httpx_mock) -> None:
    """Health check must not treat 404 endpoints as a healthy sidecar."""
    from src.voice.fish_speech_client import FishSpeechClient

    for path in ("/v1/health", "/health", "/v1/models", "/json"):
        httpx_mock.add_response(
            method="GET",
            url=f"http://127.0.0.1:8080{path}",
            status_code=404,
            text="not found",
        )

    client = FishSpeechClient(base_url="http://127.0.0.1:8080", timeout_ms=3000)
    result = await client.health_check()
    assert isinstance(result, dict)
    assert result["reachable"] is False


def test_load_reference_audio_b64_raises_on_missing() -> None:
    """Loading a missing reference audio file should raise FileNotFoundError."""
    from src.voice.fish_speech_client import FishSpeechClient

    with pytest.raises(FileNotFoundError):
        FishSpeechClient.load_reference_audio_b64("/nonexistent/path.wav")


def test_load_reference_text_raises_on_missing() -> None:
    """Loading a missing reference text file should raise FileNotFoundError."""
    from src.voice.fish_speech_client import FishSpeechClient

    with pytest.raises(FileNotFoundError):
        FishSpeechClient.load_reference_text("/nonexistent/path.txt")


def test_load_reference_text_raises_on_empty(tmp_path) -> None:
    """Loading an empty reference text file should raise ValueError."""
    from src.voice.fish_speech_client import FishSpeechClient

    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("")
    with pytest.raises(ValueError, match="empty"):
        FishSpeechClient.load_reference_text(str(empty_file))


def test_load_reference_audio_b64_succeeds(tmp_path) -> None:
    """Loading a valid WAV file should return a base64 string."""
    import base64
    from src.voice.fish_speech_client import FishSpeechClient

    wav_file = tmp_path / "test.wav"
    wav_file.write_bytes(b"RIFF" + b"\x00" * 100)
    result = FishSpeechClient.load_reference_audio_b64(str(wav_file))
    assert isinstance(result, str)
    # Verify it's valid base64
    decoded = base64.b64decode(result)
    assert decoded[:4] == b"RIFF"


def test_load_reference_text_succeeds(tmp_path) -> None:
    """Loading a valid reference text file should return its content."""
    from src.voice.fish_speech_client import FishSpeechClient

    txt_file = tmp_path / "ref.txt"
    txt_file.write_text("Halo, selamat datang.", encoding="utf-8")
    result = FishSpeechClient.load_reference_text(str(txt_file))
    assert result == "Halo, selamat datang."


# === Task 3.7: Trained Model Integration Tests ===


@pytest.mark.asyncio
async def test_synthesize_with_trained_model_adds_path_to_payload(httpx_mock, tmp_path) -> None:
    """Client should add trained_model_path to payload when trained model is available."""
    import httpx
    import msgpack
    from src.voice.fish_speech_client import FishSpeechClient

    # Create valid trained model checkpoint
    trained_dir = tmp_path / "trained"
    trained_dir.mkdir()
    (trained_dir / "model.pth").write_bytes(b"MODEL_DATA")
    (trained_dir / "config.json").write_text('{"model": "trained"}')
    (trained_dir / "tokenizer.tiktoken").write_bytes(b"TOKENIZER_DATA")

    captured: dict[str, object] = {}

    def handle_request(request: httpx.Request) -> httpx.Response:
        captured["payload"] = msgpack.unpackb(request.content, raw=False)
        return httpx.Response(200, content=b"WAVDATA")

    httpx_mock.add_callback(
        handle_request,
        method="POST",
        url="http://127.0.0.1:8080/v1/tts",
    )

    client = FishSpeechClient(
        base_url="http://127.0.0.1:8080",
        timeout_ms=3000,
        trained_model_path=str(trained_dir),
    )
    audio = await client.synthesize(
        text="halo kak",
        reference_audio_b64="eHh4",
        reference_text="halo",
    )

    assert audio == b"WAVDATA"
    payload = captured["payload"]
    assert payload["text"] == "halo kak"
    assert payload["trained_model_path"] == str(trained_dir)
    # Reference should still be included for fallback
    assert "references" in payload


@pytest.mark.asyncio
async def test_synthesize_without_trained_model_uses_zero_shot(httpx_mock) -> None:
    """Client should use zero-shot cloning when no trained model is configured."""
    import httpx
    import msgpack
    from src.voice.fish_speech_client import FishSpeechClient

    captured: dict[str, object] = {}

    def handle_request(request: httpx.Request) -> httpx.Response:
        captured["payload"] = msgpack.unpackb(request.content, raw=False)
        return httpx.Response(200, content=b"WAVDATA")

    httpx_mock.add_callback(
        handle_request,
        method="POST",
        url="http://127.0.0.1:8080/v1/tts",
    )

    client = FishSpeechClient(
        base_url="http://127.0.0.1:8080",
        timeout_ms=3000,
        trained_model_path=None,
    )
    audio = await client.synthesize(
        text="halo kak",
        reference_audio_b64="eHh4",
        reference_text="halo",
    )

    assert audio == b"WAVDATA"
    payload = captured["payload"]
    assert "trained_model_path" not in payload
    assert "references" in payload


@pytest.mark.asyncio
async def test_synthesize_with_invalid_trained_model_falls_back_to_zero_shot(httpx_mock, tmp_path) -> None:
    """Client should fall back to zero-shot when trained model checkpoint is invalid."""
    import httpx
    import msgpack
    from src.voice.fish_speech_client import FishSpeechClient

    # Create incomplete trained model checkpoint (missing files)
    trained_dir = tmp_path / "trained"
    trained_dir.mkdir()
    (trained_dir / "model.pth").write_bytes(b"MODEL_DATA")
    # Missing config.json and tokenizer.tiktoken

    captured: dict[str, object] = {}

    def handle_request(request: httpx.Request) -> httpx.Response:
        captured["payload"] = msgpack.unpackb(request.content, raw=False)
        return httpx.Response(200, content=b"WAVDATA")

    httpx_mock.add_callback(
        handle_request,
        method="POST",
        url="http://127.0.0.1:8080/v1/tts",
    )

    client = FishSpeechClient(
        base_url="http://127.0.0.1:8080",
        timeout_ms=3000,
        trained_model_path=str(trained_dir),
    )
    audio = await client.synthesize(
        text="halo kak",
        reference_audio_b64="eHh4",
        reference_text="halo",
    )

    assert audio == b"WAVDATA"
    payload = captured["payload"]
    # Should NOT include trained_model_path due to validation failure
    assert "trained_model_path" not in payload
    # Should still include references for zero-shot fallback
    assert "references" in payload


@pytest.mark.asyncio
async def test_health_check_with_trained_model_reports_availability(httpx_mock, tmp_path) -> None:
    """Health check should report trained model availability when checkpoint is valid."""
    from src.voice.fish_speech_client import FishSpeechClient

    # Create valid trained model checkpoint
    trained_dir = tmp_path / "trained"
    trained_dir.mkdir()
    (trained_dir / "model.pth").write_bytes(b"MODEL_DATA")
    (trained_dir / "config.json").write_text('{"model": "trained"}')
    (trained_dir / "tokenizer.tiktoken").write_bytes(b"TOKENIZER_DATA")

    httpx_mock.add_response(
        method="GET",
        url="http://127.0.0.1:8080/v1/health",
        status_code=200,
        json={"status": "ok"},
    )

    client = FishSpeechClient(
        base_url="http://127.0.0.1:8080",
        timeout_ms=3000,
        trained_model_path=str(trained_dir),
    )
    result = await client.health_check()

    assert isinstance(result, dict)
    assert result["reachable"] is True
    assert result["trained_model_available"] is True
    assert result["training_status"] == "completed"
    assert result["endpoint"] == "/v1/health"


@pytest.mark.asyncio
async def test_health_check_with_invalid_trained_model_reports_unavailable(httpx_mock, tmp_path) -> None:
    """Health check should report trained model unavailable when checkpoint is invalid."""
    from src.voice.fish_speech_client import FishSpeechClient

    # Create incomplete trained model checkpoint
    trained_dir = tmp_path / "trained"
    trained_dir.mkdir()
    (trained_dir / "model.pth").write_bytes(b"MODEL_DATA")
    # Missing other required files

    httpx_mock.add_response(
        method="GET",
        url="http://127.0.0.1:8080/v1/health",
        status_code=200,
        json={"status": "ok"},
    )

    client = FishSpeechClient(
        base_url="http://127.0.0.1:8080",
        timeout_ms=3000,
        trained_model_path=str(trained_dir),
    )
    result = await client.health_check()

    assert isinstance(result, dict)
    assert result["reachable"] is True
    assert result["trained_model_available"] is False
    assert result["training_status"] == "failed"


@pytest.mark.asyncio
async def test_health_check_without_trained_model_reports_not_started(httpx_mock) -> None:
    """Health check should report training_status=not_started when no trained model configured."""
    from src.voice.fish_speech_client import FishSpeechClient

    httpx_mock.add_response(
        method="GET",
        url="http://127.0.0.1:8080/v1/health",
        status_code=200,
        json={"status": "ok"},
    )

    client = FishSpeechClient(
        base_url="http://127.0.0.1:8080",
        timeout_ms=3000,
        trained_model_path=None,
    )
    result = await client.health_check()

    assert isinstance(result, dict)
    assert result["reachable"] is True
    assert result["trained_model_available"] is False
    assert result["training_status"] == "not_started"


@pytest.mark.asyncio
async def test_health_check_returns_dict_on_unreachable(httpx_mock) -> None:
    """Health check should return dict with reachable=False when server is unreachable."""
    import httpx as _httpx
    from src.voice.fish_speech_client import FishSpeechClient

    # Add exceptions for all health endpoints
    for path in ("/v1/health", "/health", "/v1/models", "/json"):
        httpx_mock.add_exception(
            _httpx.ConnectError("Connection refused"),
            url=f"http://127.0.0.1:9999{path}",
        )

    client = FishSpeechClient(base_url="http://127.0.0.1:9999", timeout_ms=1000)
    result = await client.health_check()

    assert isinstance(result, dict)
    assert result["reachable"] is False
    assert result["trained_model_available"] is False
    assert result["training_status"] == "not_started"
    assert result["endpoint"] is None


def test_validate_trained_model_checkpoint_with_valid_files(tmp_path) -> None:
    """Checkpoint validation should pass when all required files exist and are non-empty."""
    from src.voice.fish_speech_client import FishSpeechClient

    trained_dir = tmp_path / "trained"
    trained_dir.mkdir()
    (trained_dir / "model.pth").write_bytes(b"MODEL_DATA")
    (trained_dir / "config.json").write_text('{"model": "trained"}')
    (trained_dir / "tokenizer.tiktoken").write_bytes(b"TOKENIZER_DATA")

    client = FishSpeechClient(
        base_url="http://127.0.0.1:8080",
        timeout_ms=3000,
        trained_model_path=str(trained_dir),
    )

    assert client._validate_trained_model_checkpoint() is True


def test_validate_trained_model_checkpoint_with_missing_files(tmp_path) -> None:
    """Checkpoint validation should fail when required files are missing."""
    from src.voice.fish_speech_client import FishSpeechClient

    trained_dir = tmp_path / "trained"
    trained_dir.mkdir()
    (trained_dir / "model.pth").write_bytes(b"MODEL_DATA")
    # Missing config.json and tokenizer.tiktoken

    client = FishSpeechClient(
        base_url="http://127.0.0.1:8080",
        timeout_ms=3000,
        trained_model_path=str(trained_dir),
    )

    assert client._validate_trained_model_checkpoint() is False


def test_validate_trained_model_checkpoint_with_empty_files(tmp_path) -> None:
    """Checkpoint validation should fail when required files are empty."""
    from src.voice.fish_speech_client import FishSpeechClient

    trained_dir = tmp_path / "trained"
    trained_dir.mkdir()
    (trained_dir / "model.pth").write_bytes(b"")  # Empty file
    (trained_dir / "config.json").write_text('{"model": "trained"}')
    (trained_dir / "tokenizer.tiktoken").write_bytes(b"TOKENIZER_DATA")

    client = FishSpeechClient(
        base_url="http://127.0.0.1:8080",
        timeout_ms=3000,
        trained_model_path=str(trained_dir),
    )

    assert client._validate_trained_model_checkpoint() is False


def test_validate_trained_model_checkpoint_with_nonexistent_dir() -> None:
    """Checkpoint validation should fail when directory does not exist."""
    from src.voice.fish_speech_client import FishSpeechClient

    client = FishSpeechClient(
        base_url="http://127.0.0.1:8080",
        timeout_ms=3000,
        trained_model_path="/nonexistent/trained",
    )

    assert client._validate_trained_model_checkpoint() is False


def test_validate_trained_model_checkpoint_without_path() -> None:
    """Checkpoint validation should return False when no trained_model_path is configured."""
    from src.voice.fish_speech_client import FishSpeechClient

    client = FishSpeechClient(
        base_url="http://127.0.0.1:8080",
        timeout_ms=3000,
        trained_model_path=None,
    )

    assert client._validate_trained_model_checkpoint() is False
