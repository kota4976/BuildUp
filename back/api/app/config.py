"""Application configuration using Pydantic Settings"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Database
    database_url: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "buildup"
    postgres_user: str = "buildup_user"
    postgres_password: str = "postgres"
    
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
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated CORS origins to list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.app_env.lower() == "production"


# Global settings instance
settings = Settings()

