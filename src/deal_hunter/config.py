from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    LLM_PROVIDER: Literal["vllm", "ollama", "openai"] = "ollama"
    LLM_BASE_URL: str = "http://localhost:11434/v1"
    LLM_MODEL: str = "gemma3:4b"
    LLM_API_KEY: str = "no-key"

    SERPAPI_KEY: str | None = None
    USE_MOCK_DATA: bool = False
    MOCK_DATA_DIR: Path = Path("mock_data")

    OUTPUT_DIR: Path = Path("reports")
    DB_PATH: Path = Path("price_history.db")

    RETAILERS: str = "amazon,costco,walmart,bestbuy"

    @property
    def retailer_list(self) -> list[str]:
        return [r.strip() for r in self.RETAILERS.split(",")]

    @property
    def should_use_mock(self) -> bool:
        return self.USE_MOCK_DATA or not self.SERPAPI_KEY
