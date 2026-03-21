"""
Configuración centralizada usando pydantic-settings.
Patrón Singleton via @lru_cache para garantizar una sola instancia.
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Todas las variables de entorno de la aplicación.
    pydantic-settings las carga automáticamente del entorno / archivo .env.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",           # Ignora variables no declaradas
    )

    # ── Entorno ──────────────────────────────────────────────────────────────
    environment: Literal["development", "staging", "production", "test"] = "development"
    port: int = Field(default=8000, ge=1, le=65535)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # ── OpenAI ────────────────────────────────────────────────────────────────
    openai_api_key: SecretStr = Field(..., description="Clave API de OpenAI")
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    openai_max_tokens: int = Field(default=1024, ge=1)
    openai_max_retries: int = Field(default=3, ge=1, le=10)

    # ── OpenWeatherMap ────────────────────────────────────────────────────────
    openweather_api_key: SecretStr = Field(..., description="Clave API de OpenWeatherMap")
    openweather_base_url: str = "https://api.openweathermap.org/data/2.5"
    openweather_units: Literal["metric", "imperial", "standard"] = "metric"
    openweather_lang: str = "es"

    # ── API ───────────────────────────────────────────────────────────────────
    api_prefix: str = "/api/v1"
    api_title: str = "My GenAI App"
    api_version: str = "0.1.0"
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"]
    )

    # ── LangGraph ─────────────────────────────────────────────────────────────
    langgraph_recursion_limit: int = Field(default=10, ge=1, le=50)

    # ── Propiedades computadas ────────────────────────────────────────────────
    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_testing(self) -> bool:
        return self.environment == "test"

    @field_validator("openai_model")
    @classmethod
    def validate_openai_model(cls, v: str) -> str:
        allowed = {
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
        }
        if v not in allowed:
            raise ValueError(f"Modelo no soportado: {v}. Permitidos: {allowed}")
        return v

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Validaciones adicionales para entornos de producción."""
        if self.environment == "production":
            if self.log_level == "DEBUG":
                raise ValueError(
                    "LOG_LEVEL=DEBUG no está permitido en producción."
                )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Singleton de Settings.
    Usar get_settings() en lugar de instanciar Settings() directamente.
    El decorador @lru_cache garantiza que solo se crea una instancia.
    """
    return Settings()  # type: ignore[call-arg]