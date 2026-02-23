from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    name: str = "sonicaid"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: Literal["debug", "info", "warning", "error"] = "info"


class MlSettings(BaseSettings):
    model_path: Path = Path("ml/artifacts/sonicaid_multitask.pt")
    device: Literal["cpu", "cuda"] = "cpu"


class StreamingSettings(BaseSettings):
    sample_rate: int = 16000
    window_seconds: float = 1.0
    hop_seconds: float = 0.5
    max_session_seconds: int = 3600


class PrivacySettings(BaseSettings):
    enable_anonymization: bool = True
    store_raw_audio: bool = False


class Settings(BaseSettings):
    app: AppSettings = AppSettings()
    ml: MlSettings = MlSettings()
    streaming: StreamingSettings = StreamingSettings()
    privacy: PrivacySettings = PrivacySettings()

    env: Literal["dev", "prod"] = Field(default="dev", validation_alias="SONICAID_ENV")

    class Config:
        env_prefix = "SONICAID_"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

