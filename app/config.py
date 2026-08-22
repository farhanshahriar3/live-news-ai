from functools import lru_cache
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gemini_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("GEMINI_API_KEY", "OPENAI_API_KEY"),
    )
    gemini_model: str = Field(
        default="gemini-3.7-flash",
        validation_alias=AliasChoices("GEMINI_MODEL"),
    )
    tavily_api_key: SecretStr | None = Field(default=None, validation_alias="TAVILY_API_KEY")
    app_env: str = Field(default="development", validation_alias="APP_ENV")
    app_host: str = Field(default="127.0.0.1", validation_alias="APP_HOST")
    app_port: int = Field(default=8000, validation_alias="APP_PORT")
    streamlit_api_url: str = Field(
        default="http://127.0.0.1:8000", validation_alias="STREAMLIT_API_URL"
    )
    app_timezone: str = Field(default="UTC", validation_alias="APP_TIMEZONE")
    max_search_results: int = Field(default=8, validation_alias="MAX_SEARCH_RESULTS", ge=1, le=20)
    max_sources_per_answer: int = Field(
        default=6, validation_alias="MAX_SOURCES_PER_ANSWER", ge=1, le=20
    )
    max_article_content_chars: int = Field(
        default=12000, validation_alias="MAX_ARTICLE_CONTENT_CHARS", ge=1000
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    @field_validator("app_timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"Unknown APP_TIMEZONE: {value}") from exc
        return value

    def require_gemini_key(self) -> str:
        if not self.gemini_configured:
            raise RuntimeError(
                "GEMINI_API_KEY is missing. Add it to your .env file "
                "(OPENAI_API_KEY is accepted as a legacy alias)."
            )
        return self.gemini_api_key.get_secret_value().strip()

    @property
    def gemini_configured(self) -> bool:
        return bool(self.gemini_api_key and self.gemini_api_key.get_secret_value().strip())

    @property
    def openai_configured(self) -> bool:
        return self.gemini_configured

    def require_openai_key(self) -> str:
        return self.require_gemini_key()

    @property
    def search_configured(self) -> bool:
        return bool(self.tavily_api_key and self.tavily_api_key.get_secret_value().strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
