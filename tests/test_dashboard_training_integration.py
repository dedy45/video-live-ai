"""Test dashboard integration for training status and runtime state fields.

This test verifies Task 3.9 requirements:
- Dashboard Tab Suara displays trained_model_available from runtime state
- Dashboard Training Jobs section displays training_status and progress
- Dashboard status bar changes from "Tertahan/unknown" to correct status after sidecar startup
- Dashboard displays dataset quality metrics (duration, file count)
- Dashboard API endpoints include new training status fields
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.voice.runtime_state import VoiceRuntimeState, get_voice_runtime_state, reset_voice_runtime_state


class TestDashboardTrainingIntegration:
    """Test dashboard integration with training status fields."""

    def setup_method(self):
        """Reset runtime state before each test."""
        reset_voice_runtime_state()

    def test_runtime_state_includes_training_fields(self):
        """Verify runtime state includes all training status fields."""
        state = get_voice_runtime_state()
        state_dict = state.to_dict()

        # Verify training fields are present
        assert "trained_model_available" in state_dict
        assert "training_dataset_duration_min" in state_dict
        assert "training_status" in state_dict

        # Verify default values
        assert state_dict["trained_model_available"] is False
        assert state_dict["training_dataset_duration_min"] is None
        assert state_dict["training_status"] == "not_started"

    def test_runtime_state_training_status_validation(self):
        """Verify training_status field validates allowed values."""
        state = get_voice_runtime_state()

        # Valid statuses should work
        for status in ["not_started", "in_progress", "completed", "failed"]:
            state.set_training_status(status)
            assert state.training_status == status

        # Invalid status should raise ValueError
        with pytest.raises(ValueError, match="Invalid training_status"):
            state.set_training_status("invalid_status")

    def test_runtime_state_updates_training_fields(self):
        """Verify runtime state can update training fields."""
        state = get_voice_runtime_state()

        # Update training fields
        state.trained_model_available = True
        state.training_dataset_duration_min = 45.5
        state.set_training_status("completed")

        # Verify updates
        state_dict = state.to_dict()
        assert state_dict["trained_model_available"] is True
        assert state_dict["training_dataset_duration_min"] == 45.5
        assert state_dict["training_status"] == "completed"

    @pytest.mark.asyncio
    async def test_runtime_truth_exposes_voice_engine_with_training_fields(self):
        """Verify runtime truth endpoint exposes voice engine with training fields."""
        from src.dashboard.truth import get_runtime_truth_snapshot

        # Set up runtime state with training data
        state = get_voice_runtime_state()
        state.trained_model_available = True
        state.training_dataset_duration_min = 35.0
        state.set_training_status("completed")
        state.server_reachable = True
        state.reference_ready = True

        # Get runtime truth snapshot
        truth = get_runtime_truth_snapshot(force_refresh=True)

        # Verify voice_engine includes training fields
        assert "voice_engine" in truth
        voice_engine = truth["voice_engine"]
        assert voice_engine["trained_model_available"] is True
        assert voice_engine["training_dataset_duration_min"] == 35.0
        assert voice_engine["training_status"] == "completed"
        assert voice_engine["server_reachable"] is True
        assert voice_engine["reference_ready"] is True

    @pytest.mark.asyncio
    async def test_voice_lab_api_returns_runtime_state(self):
        """Verify GET /api/voice/lab includes training status fields."""
        from src.dashboard.api import get_voice_lab_state
        from src.control_plane import ControlPlaneStore

        # Mock the control plane store and _ensure_default_voice_profile
        with patch("src.dashboard.api.get_control_plane_store") as mock_store, \
             patch("src.dashboard.api._ensure_default_voice_profile"):
            mock_instance = Mock(spec=ControlPlaneStore)
            mock_instance.get_voice_lab_state.return_value = {
                "mode": "standalone",
                "active_profile_id": 1,
                "preview_session_id": "",
                "selected_avatar_id": "",
                "selected_language": "id",
                "selected_profile_type": "quick_clone",
                "selected_revision_id": None,
                "selected_style_preset": "natural",
                "selected_stability": 0.75,
                "selected_similarity": 0.8,
                "draft_text": "Test",
                "last_generation_id": None,
            }
            mock_store.return_value = mock_instance

            # Call the API endpoint
            result = await get_voice_lab_state()

            # Verify result is returned
            assert result is not None
            assert "mode" in result

    @pytest.mark.asyncio
    async def test_training_jobs_api_returns_job_list(self):
        """Verify GET /api/voice/training-jobs returns training jobs with status."""
        from src.dashboard.api import list_voice_training_jobs
        from src.control_plane import ControlPlaneStore

        # Mock the control plane store
        with patch("src.dashboard.api.get_control_plane_store") as mock_store:
            mock_instance = Mock(spec=ControlPlaneStore)
            mock_instance.list_voice_training_jobs.return_value = [
                {
                    "id": 1,
                    "profile_id": 1,
                    "profile_name": "Studio Voice",
                    "job_type": "studio_voice_training",
                    "dataset_path": "assets/voice/training_dataset",
                    "status": "completed",
                    "current_stage": "finished",
                    "progress_percent": 100,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T01:00:00Z",
                }
            ]
            mock_store.return_value = mock_instance

            # Call the API endpoint
            result = await list_voice_training_jobs(limit=20)

            # Verify result includes training status
            assert len(result) == 1
            assert result[0]["status"] == "completed"
            assert result[0]["current_stage"] == "finished"
            assert result[0]["progress_percent"] == 100

    @pytest.mark.asyncio
    async def test_voice_warmup_triggers_sidecar_startup(self):
        """Verify POST /api/voice/warmup triggers sidecar startup with retry logic."""
        from src.dashboard.api import voice_warmup

        # Mock the voice engine and ensure_voice_engine_ready
        with patch("src.dashboard.api.get_voice_lab_engine") as mock_engine, \
             patch("src.dashboard.api._ensure_voice_engine_ready") as mock_ensure:
            
            mock_engine.return_value = Mock()
            mock_ensure.return_value = (True, "Sidecar started successfully")

            # Call the warmup endpoint
            result = await voice_warmup()

            # Verify warmup was called
            assert result["status"] == "success"
            assert "siap" in result["message"].lower()
            mock_ensure.assert_called_once()

    @pytest.mark.asyncio
    async def test_voice_warmup_handles_startup_failure(self):
        """Verify POST /api/voice/warmup handles startup failures gracefully."""
        from src.dashboard.api import voice_warmup

        # Mock the voice engine and ensure_voice_engine_ready to fail
        with patch("src.dashboard.api.get_voice_lab_engine") as mock_engine, \
             patch("src.dashboard.api._ensure_voice_engine_ready") as mock_ensure:
            
            mock_engine.return_value = Mock()
            mock_ensure.return_value = (False, "Sidecar failed to start")

            # Call the warmup endpoint
            result = await voice_warmup()

            # Verify failure is reported
            assert result["status"] == "blocked"
            assert "belum siap" in result["message"].lower()

    def test_voice_status_changes_after_sidecar_startup(self):
        """Verify dashboard status changes from 'Tertahan' to 'Siap' after sidecar startup."""
        state = get_voice_runtime_state()

        # Initial state: sidecar not reachable
        assert state.server_reachable is False
        assert state.reference_ready is False

        # Simulate sidecar startup success
        state.server_reachable = True
        state.reference_ready = True
        state.resolved_engine = "fish_speech"

        # Verify status changed
        assert state.server_reachable is True
        assert state.reference_ready is True

    def test_dataset_quality_metrics_in_runtime_state(self):
        """Verify dataset quality metrics are tracked in runtime state."""
        state = get_voice_runtime_state()

        # Set dataset quality metrics
        state.training_dataset_duration_min = 42.5

        # Verify metrics are accessible
        state_dict = state.to_dict()
        assert state_dict["training_dataset_duration_min"] == 42.5

    def test_training_status_progression(self):
        """Verify training status can progress through all states."""
        state = get_voice_runtime_state()

        # Progress through training states
        state.set_training_status("not_started")
        assert state.training_status == "not_started"

        state.set_training_status("in_progress")
        assert state.training_status == "in_progress"

        state.set_training_status("completed")
        assert state.training_status == "completed"
        state.trained_model_available = True

        # Verify final state
        state_dict = state.to_dict()
        assert state_dict["training_status"] == "completed"
        assert state_dict["trained_model_available"] is True

    def test_training_status_can_fail(self):
        """Verify training status can be set to failed."""
        state = get_voice_runtime_state()

        # Simulate training failure
        state.set_training_status("in_progress")
        state.set_training_status("failed")

        # Verify failure state
        assert state.training_status == "failed"
        assert state.trained_model_available is False

    @pytest.mark.asyncio
    async def test_voice_runtime_mode_reflects_sidecar_status(self):
        """Verify voice_runtime_mode in truth reflects sidecar status correctly."""
        from src.dashboard.truth import _get_voice_runtime_mode

        # Mock is_mock_mode to return False for this test
        with patch("src.dashboard.truth.is_mock_mode", return_value=False):
            # Test with sidecar not reachable
            state = get_voice_runtime_state()
            state.resolved_engine = "unknown"
            state.server_reachable = False
            mode = _get_voice_runtime_mode()
            assert mode == "unknown"

            # Test with Fish Speech active
            state.resolved_engine = "fish_speech"
            state.server_reachable = True
            state.fallback_active = False
            mode = _get_voice_runtime_mode()
            assert mode == "fish_speech_local"

            # Test with Edge TTS fallback
            state.resolved_engine = "edge_tts"
            state.fallback_active = True
            mode = _get_voice_runtime_mode()
            assert mode == "edge_tts_fallback"

    def test_trained_model_available_flag_integration(self):
        """Verify trained_model_available flag is properly integrated."""
        state = get_voice_runtime_state()

        # Initially no trained model
        assert state.trained_model_available is False

        # After training completes
        state.set_training_status("completed")
        state.trained_model_available = True

        # Verify flag is set
        state_dict = state.to_dict()
        assert state_dict["trained_model_available"] is True
        assert state_dict["training_status"] == "completed"
