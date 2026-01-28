"""
Application configuration settings
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AliasChoices, Field, field_validator
from typing import List, Union


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database
    database_url: str = "sqlite:///./dux.db"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    upload_dir: str = "./uploads"
    evaluation_dir: str = "./evaluations"
    debug: bool = False  # Set to True to show detailed error messages
    log_level: str = "INFO"  # Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL

    # Session Configuration
    session_secret: str = "change-this-secret-in-production"  # IMPORTANT: Set in .env for production
    session_cookie_name: str = "dux_session"
    session_max_age: int = 86400  # 24 hours in seconds
    session_cookie_secure: bool = True  # Set to True in production with HTTPS
    session_cookie_httponly: bool = True
    session_cookie_samesite: str = "lax"  # "strict", "lax", or "none"

    # CORS Configuration
    cors_origins: Union[List[str], str] = ["http://localhost:5173"]
    cors_allow_credentials: bool = True

    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            # Handle comma-separated string
            if ',' in v:
                return [origin.strip() for origin in v.split(',')]
            # Handle single origin
            return [v.strip()]
        return v

    # WebAuthn / Passkey Configuration
    rp_id: str = "localhost"
    rp_name: str = "Dux"
    origin: str = "http://localhost:5173"

    # Security
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    challenge_timeout_minutes: int = 5

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60

    # Password Policy
    password_min_length: int = 12
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_digit: bool = True
    password_require_special: bool = True

    # Linkedin OAuth
    linkedin_client_id: str = ""
    linkedin_client_secret: str = ""
    linkedin_redirect_uri: str = "http://localhost:5173/linkedin/callback"

    # France Travail OAuth
    ft_client_id: str = ""
    ft_client_secret: str = ""
    # France Travail API Configuration
    ft_auth_url: str = ""
    ft_api_url_offres: str = ""
    ft_api_url_fiche_metier: str = ""
    ft_api_url_code_metier: str = ""
    ft_api_url_fiche_competence: str = ""
    ft_api_url_code_competence: str = ""

    # LLM Configuration
    openai_api_key: str = ""
    openai_model: str = ""
    openai_base_url: str = ""

    # VLM Configuration (hosted API) — accepts VLM_API_KEY or VLM_KEY from env
    vlm_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("vlm_api_key", "vlm_key"),
    )
    vlm_model: str = "Qwen2.5-VL-7B-Instruct"
    vlm_base_url: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Global settings instance
settings = Settings()
