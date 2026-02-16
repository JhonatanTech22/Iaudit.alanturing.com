"""IAudit - Configuration from environment variables."""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    # Supabase
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_key: str = Field(..., description="Supabase service role key")

    # InfoSimples
    infosimples_token: str = Field(..., description="InfoSimples API token")

    # Google Drive
    google_drive_credentials_path: str = Field(
        "./credentials/service-account.json",
        description="Path to Google Drive service account JSON",
    )
    google_drive_root_folder_id: str = Field(
        "", description="Root folder ID in Google Drive"
    )

    # Email - Resend
    resend_api_key: str = Field("", description="Resend API key")
    email_from: str = Field(
        "noreply@iaudit.allanturing.com", description="Sender email"
    )

    # Email - SMTP fallback
    smtp_host: str = Field("smtp.gmail.com")
    smtp_port: int = Field(587)
    smtp_user: str = Field("")
    smtp_password: str = Field("")

    # App
    app_name: str = Field("IAudit")
    api_host: str = Field("0.0.0.0")
    api_port: int = Field(8000)
    frontend_url: str = Field("http://localhost:8501")
    backend_url: str = Field("http://localhost:8000")

    # Scheduler
    scheduler_poll_interval_minutes: int = Field(5)
    scheduler_daily_hour: int = Field(0)
    scheduler_daily_minute: int = Field(5)

    # Rate limiting & retry
    rate_limit_seconds: int = Field(3)
    max_retries: int = Field(3)
    retry_interval_minutes: int = Field(5)

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
