import pytest

from app.config import Settings


def test_missing_gemini_key_is_clear():
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        Settings(_env_file=None).require_gemini_key()


def test_valid_configuration():
    settings = Settings(OPENAI_API_KEY="secret", TAVILY_API_KEY="search")
    assert settings.require_gemini_key() == "secret"
    assert settings.search_configured


def test_authorization_api_key_is_treated_as_opaque():
    settings = Settings(OPENAI_API_KEY="AQ.oauth-token")
    assert settings.require_gemini_key() == "AQ.oauth-token"
