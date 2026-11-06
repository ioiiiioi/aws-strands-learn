from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_DSN:str = "postgresql://postgres:password@localhost:5432/skillsbary"
    APP_ENV:str = "development"

    # LLM lokal (OpenAI-compatible lewat LiteLLM)
    STRANDS_MODEL: str = "openai/deepseek/deepseek-flash"
    OPENAI_BASE_URL: str = "http://localhost:20128/v1"
    OPENAI_API_KEY: str = "dummy"

    # Jalur AWS asli
    USE_BEDROCK: bool = False
    AWS_REGION: str = "us-east-1"
    BEDROCK_MODEL_ID: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"

settings = Settings()