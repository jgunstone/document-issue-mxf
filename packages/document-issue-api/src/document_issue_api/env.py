import pathlib

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

FPTH_ENV = pathlib.Path(__file__).parents[2] / "api-dev.env"


class ApiEnv(BaseSettings):
    DOCUMENTISSUE_DATABASE_URL: str = Field(
        "sqlite:///./document-issue.db",
        description="url to sqlite file",
    )
    model_config = SettingsConfigDict(env_file=FPTH_ENV, env_file_encoding="utf-8")
