from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.app.core.config import MlSettings, Settings, StreamingSettings


def test_settings_accept_explicit_runtime_environment(monkeypatch):
    monkeypatch.setenv("SONICAID_ENV", "prod")
    settings = Settings()
    assert settings.env == "prod"


def test_model_path_configuration_is_supported():
    settings = MlSettings(model_path=Path("weights/model.pt"))
    assert settings.model_path == Path("weights/model.pt")


@pytest.mark.parametrize("bad_seconds", [0, -1, 61])
def test_chunk_duration_limits_are_enforced(bad_seconds):
    with pytest.raises(ValidationError):
        StreamingSettings(max_chunk_seconds=bad_seconds)
