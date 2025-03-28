import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseSettings, SecretStr, field_validator, Field

# Get the path to the config.yaml file
CONFIG_PATH = Path(__file__).parent / "config.yaml"


class Settings(BaseSettings):
    """Application settings configured with YAML and environment variables.
    
    Environment variables take precedence over YAML configuration.
    """

    # Database settings
    POSTGRES_HOST: str = Field("localhost", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(5432, description="PostgreSQL port")
    POSTGRES_USER: str = Field(..., description="PostgreSQL username")
    POSTGRES_PASSWORD: SecretStr = Field(..., description="PostgreSQL password")
    POSTGRES_DB: str = Field(..., description="PostgreSQL database name")
    
    # MinIO settings
    MINIO_ENDPOINT: str = Field(..., description="MinIO endpoint URL")
    MINIO_ACCESS_KEY: str = Field(..., description="MinIO access key")
    MINIO_SECRET_KEY: SecretStr = Field(..., description="MinIO secret key")
    MINIO_BUCKET_NAME: str = Field("webex-recordings", description="MinIO bucket name")
    MINIO_SECURE: bool = Field(True, description="Use HTTPS for MinIO")
    
    # Webex settings
    WEBEX_SITE_URL: str = Field(..., description="Webex site URL")
    WEBEX_API_KEY: SecretStr = Field(..., description="Webex API key")
    
    # Batch job settings
    BATCH_JOB_INTERVAL_MINUTES: int = Field(60, description="Batch job interval in minutes")
    
    # Logging settings
    LOG_LEVEL: str = Field("INFO", description="Logging level")
    LOG_FORMAT: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Logging format"
    )
    
    # Prefect settings
    PREFECT_API_URL: Optional[str] = Field(None, description="Prefect API URL")
    
    @field_validator("LOG_LEVEL")
    def validate_log_level(cls, v: str) -> str:
        """Validate that the log level is a valid Python logging level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()
    
    class Config:
        env_file = ".env"
        extra = "ignore"


def load_yaml_config() -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if not CONFIG_PATH.exists():
        return {}
    
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f) or {}


def get_settings() -> Settings:
    """Get application settings from YAML and environment variables."""
    yaml_config = load_yaml_config()
    
    # Convert nested dictionaries to flat format with uppercase keys
    flat_config = {}
    
    def flatten_dict(d, parent_key=""):
        for k, v in d.items():
            new_key = f"{parent_key}_{k}".upper() if parent_key else k.upper()
            if isinstance(v, dict):
                flatten_dict(v, new_key)
            else:
                flat_config[new_key] = v
    
    flatten_dict(yaml_config)
    
    # Set environment variables from YAML (won't override existing env vars)
    for key, value in flat_config.items():
        if key not in os.environ and value is not None:
            os.environ[key] = str(value)
    
    return Settings()


# Create a settings instance
settings = get_settings()