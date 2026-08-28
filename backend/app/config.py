import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./internship_copilot.db")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")


settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
