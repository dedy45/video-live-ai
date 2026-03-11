from __future__ import annotations

from unittest.mock import patch


def test_main_uses_dashboard_env_override(monkeypatch):
    import src.config.loader as loader
    from src import main as main_module

    loader._config = None
    loader._env = None
    monkeypatch.setenv("DASHBOARD_HOST", "127.0.0.1")
    monkeypatch.setenv("DASHBOARD_PORT", "8001")

    with patch.object(main_module, "create_app", return_value="app"), patch.object(main_module.uvicorn, "run") as run_mock:
        main_module.main()

    assert run_mock.call_count == 1
    assert run_mock.call_args.kwargs["host"] == "127.0.0.1"
    assert run_mock.call_args.kwargs["port"] == 8001
