"""Test configuration — shared fixtures and settings."""

from __future__ import annotations

import os

import pytest

# Always run tests in Mock Mode
os.environ["MOCK_MODE"] = "true"
os.environ["ENV"] = "development"
