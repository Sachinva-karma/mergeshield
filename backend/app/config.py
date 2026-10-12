import os
import subprocess
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # GitHub
    GITHUB_TOKEN: Optional[str] = None

    # Model Provider: "groq", "openrouter", "together", "openai_compatible"
    MODEL_PROVIDER: str = "groq"
    MODEL_NAME: str = "openai/gpt-oss-120b"
    
    # Provider Keys
    GROQ_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    TOGETHER_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None

    # Diff bounds to prevent oversized payload & token exhaustion
    MAX_DIFF_LINES: int = 1500
    MAX_DIFF_BYTES: int = 200_000

    def get_github_token(self) -> Optional[str]:
        if self.GITHUB_TOKEN:
            return self.GITHUB_TOKEN
        # Check standard environment variable GH_TOKEN
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if token:
            return token
        # Fallback to local gh CLI if available
        try:
            res = subprocess.run(
                ["gh", "auth", "token"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            pass
        return None

    def get_model_api_key(self) -> Optional[str]:
        provider = self.MODEL_PROVIDER.lower()
        if provider == "groq":
            return self.GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
        if provider == "openrouter":
            return self.OPENROUTER_API_KEY or os.environ.get("OPENROUTER_API_KEY")
        if provider == "together":
            return self.TOGETHER_API_KEY or os.environ.get("TOGETHER_API_KEY")
        return self.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")


from dotenv import load_dotenv

def get_settings() -> Settings:
    load_dotenv(override=True)
    return Settings()
