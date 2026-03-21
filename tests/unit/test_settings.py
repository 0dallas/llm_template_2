"""Tests unitarios para la configuración."""
import pytest
from pydantic import ValidationError

from my_genai_app.config.settings import Settings, get_settings


class TestSettings:
    """Tests de la clase Settings."""

    def test_get_settings_returns_singleton(self):
        """get_settings() debe retornar siempre la misma instancia."""
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

    def test_default_environment_is_test(self):
        """En el entorno de test, ENVIRONMENT debe ser 'test'."""
        settings = get_settings()
        assert settings.environment == "test"

    def test_is_testing_property(self):
        settings = get_settings()
        assert settings.is_testing is True

    def test_is_production_property(self):
        settings = get_settings()
        assert settings.is_production is False

    def test_openai_api_key_is_secret(self):
        """La clave API no debe exponerse como string plano."""
        settings = get_settings()
        # SecretStr no muestra el valor en repr
        assert "sk-test-fake-key" not in str(settings.openai_api_key)
        # Pero sí se puede obtener con get_secret_value()
        assert settings.openai_api_key.get_secret_value() == "sk-test-fake-key"

    def test_port_default_value(self):
        settings = get_settings()
        assert settings.port == 8000

    def test_api_prefix(self):
        settings = get_settings()
        assert settings.api_prefix == "/api/v1"

    def test_invalid_openai_model_raises(self, monkeypatch):
        """Modelo OpenAI no soportado debe lanzar ValidationError."""
        monkeypatch.setenv("OPENAI_MODEL", "gpt-invalid-model")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("OPENWEATHER_API_KEY", "fake-key")
        with pytest.raises(ValidationError, match="Modelo no soportado"):
            Settings(  # type: ignore[call-arg]
                openai_api_key="sk-test",
                openweather_api_key="fake-key",
                openai_model="gpt-invalid-model",
            )

    def test_temperature_bounds(self):
        """La temperatura debe estar entre 0.0 y 2.0."""
        with pytest.raises(ValidationError):
            Settings(  # type: ignore[call-arg]
                openai_api_key="sk-test",
                openweather_api_key="fake-key",
                openai_temperature=3.0,  # Inválido
            )