"""Tests for training status fields in VoiceRuntimeState.

Task 3.3: Add training status fields to runtime state
"""

import pytest

from src.voice.runtime_state import VoiceRuntimeState, get_voice_runtime_state, reset_voice_runtime_state


def test_training_fields_default_values():
    """Test that new training fields have correct default values."""
    state = VoiceRuntimeState()
    
    assert state.trained_model_available is False
    assert state.training_dataset_duration_min is None
    assert state.training_status == "not_started"


def test_training_fields_in_to_dict():
    """Test that new training fields are included in to_dict() output."""
    state = VoiceRuntimeState()
    state.trained_model_available = True
    state.training_dataset_duration_min = 45.5
    state.training_status = "completed"
    
    result = state.to_dict()
    
    assert "trained_model_available" in result
    assert "training_dataset_duration_min" in result
    assert "training_status" in result
    assert result["trained_model_available"] is True
    assert result["training_dataset_duration_min"] == 45.5
    assert result["training_status"] == "completed"


def test_training_status_validation_valid_values():
    """Test that valid training_status values are accepted."""
    valid_statuses = ["not_started", "in_progress", "completed", "failed"]
    
    for status in valid_statuses:
        state = VoiceRuntimeState(training_status=status)
        assert state.training_status == status


def test_training_status_validation_invalid_value():
    """Test that invalid training_status values raise ValueError."""
    with pytest.raises(ValueError, match="Invalid training_status"):
        VoiceRuntimeState(training_status="invalid_status")


def test_set_training_status_valid():
    """Test set_training_status() with valid values."""
    state = VoiceRuntimeState()
    
    state.set_training_status("in_progress")
    assert state.training_status == "in_progress"
    
    state.set_training_status("completed")
    assert state.training_status == "completed"
    
    state.set_training_status("failed")
    assert state.training_status == "failed"


def test_set_training_status_invalid():
    """Test set_training_status() with invalid value raises ValueError."""
    state = VoiceRuntimeState()
    
    with pytest.raises(ValueError, match="Invalid training_status"):
        state.set_training_status("unknown_status")


def test_training_fields_with_existing_fields():
    """Test that new training fields work alongside existing fields."""
    state = VoiceRuntimeState()
    
    # Set existing fields
    state.requested_engine = "fish_speech"
    state.server_reachable = True
    state.reference_ready = True
    
    # Set new training fields
    state.trained_model_available = True
    state.training_dataset_duration_min = 60.0
    state.set_training_status("completed")
    
    # Verify all fields are preserved
    result = state.to_dict()
    assert result["requested_engine"] == "fish_speech"
    assert result["server_reachable"] is True
    assert result["reference_ready"] is True
    assert result["trained_model_available"] is True
    assert result["training_dataset_duration_min"] == 60.0
    assert result["training_status"] == "completed"


def test_singleton_preserves_training_fields():
    """Test that singleton get_voice_runtime_state() preserves training fields."""
    reset_voice_runtime_state()
    
    state = get_voice_runtime_state()
    state.trained_model_available = True
    state.training_dataset_duration_min = 35.0
    state.set_training_status("in_progress")
    
    # Get singleton again
    state2 = get_voice_runtime_state()
    
    # Verify same instance with preserved values
    assert state2 is state
    assert state2.trained_model_available is True
    assert state2.training_dataset_duration_min == 35.0
    assert state2.training_status == "in_progress"
    
    # Cleanup
    reset_voice_runtime_state()


def test_update_methods_preserve_training_fields():
    """Test that existing update methods don't interfere with training fields."""
    state = VoiceRuntimeState()
    
    # Set training fields
    state.trained_model_available = True
    state.training_dataset_duration_min = 50.0
    state.set_training_status("completed")
    
    # Call existing update methods
    state.update_success("fish_speech", 2500.0)
    
    # Verify training fields are preserved
    assert state.trained_model_available is True
    assert state.training_dataset_duration_min == 50.0
    assert state.training_status == "completed"
    
    # Verify existing fields are updated correctly
    assert state.resolved_engine == "fish_speech"
    assert state.last_latency_ms == 2500.0
    assert state.server_reachable is True
