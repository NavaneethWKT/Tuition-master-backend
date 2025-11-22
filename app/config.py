from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "aprameyar"
    DB_PASSWORD: str = ""
    DB_NAME: str = "tuition_master_db"
    
    # Supabase settings
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""  # Service role key for server-side operations
    SUPABASE_STORAGE_BUCKET: str = "documents"  # Default bucket name
    
    # AI Service settings
    AI_SERVICE_URL: str = "https://nonzealous-vectorially-adolfo.ngrok-free.dev"  # AI service URL for webhook calls
    
    @property
    def DATABASE_URL(self) -> str:
        if self.DB_PASSWORD:
            return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        else:
            return f"postgresql://{self.DB_USER}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

