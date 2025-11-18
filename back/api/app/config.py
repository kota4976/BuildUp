"""Application configuration using Pydantic Settings"""
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Database routing
    database_url: Optional[str] = None
    database_target: str = "dev"  # dev (SSH) or docker (local container)
    runtime_context: str = "local"  # local (host) or docker (container)
    database_url_docker: Optional[str] = None
    database_url_dev_local: Optional[str] = None
    database_url_dev_docker: Optional[str] = None
    
    # GitHub OAuth
    github_client_id: str
    github_client_secret: str
    github_redirect_uri: str
    
    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 43200  # 30 days
    
    # Application
    app_name: str = "BuildUp"
    app_env: str = "development"
    cors_origins: str = "http://localhost,http://localhost:80,http://localhost:5500,127.0.0.1:5500"
    
    # Server
    api_host: str = "127.0.0.1"
    api_port: int = 8080

    @property
    def database_url_resolved(self) -> str:
        """
        Determine the effective database URL based on target and runtime context.
        Priority order:
            1. Explicit DATABASE_URL
            2. Preset matched by DATABASE_TARGET and RUNTIME_CONTEXT
        """
        if self.database_url:
            return self.database_url

        target = self.database_target.lower()
        context = self.runtime_context.lower()

        if target == "docker":
            if not self.database_url_docker:
                raise ValueError("DATABASE_URL_DOCKER is not configured")
            return self.database_url_docker

        if target == "dev":
            if context == "docker":
                if not self.database_url_dev_docker:
                    raise ValueError("DATABASE_URL_DEV_DOCKER is not configured")
                return self.database_url_dev_docker
            if not self.database_url_dev_local:
                raise ValueError("DATABASE_URL_DEV_LOCAL is not configured")
            return self.database_url_dev_local

        raise ValueError(f"Unsupported DATABASE_TARGET '{self.database_target}'")
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated CORS origins to list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.app_env.lower() == "production"


# Global settings instance
settings = Settings()

