import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    APP_NAME: str = "Specter AI Code Review Engine"
    APP_VERSION: str = "1.0.0"
    ENGINEER: str = "Divyansh Mishra"
    
    # Base paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DB_PATH: Path = BASE_DIR / "specter_reviews.db"
    STORAGE_DIR: Path = BASE_DIR / "workspace_storage"
    BENCHMARKS_DIR: Path = BASE_DIR / "benchmarks"
    
    # LLM Settings
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    DEFAULT_MODEL: str = "qwen/qwen3.8-27b"
    LLM_TEMPERATURE: float = 0.1
    
    # Agent Guardrails
    MAX_ITERATIONS: int = 10
    TOOL_TIMEOUT_SECONDS: int = 15
    CONFIDENCE_THRESHOLD: float = 0.80  # below this is marked suggestion_only
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Sandbox limits
    MAX_FILE_SIZE_BYTES: int = 1_000_000  # 1MB
    MAX_SCAN_FILES: int = 500

settings = Settings()
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
settings.BENCHMARKS_DIR.mkdir(parents=True, exist_ok=True)
