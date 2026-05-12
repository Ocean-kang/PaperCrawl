import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    CACHE_DIR: Path = Path(os.getenv("CACHE_DIR", BASE_DIR / "cache"))
    OUTPUT_DIR: Path = Path(os.getenv("OUTPUT_DIR", BASE_DIR / "output"))
    DEBUG_DIR: Path = Path(os.getenv("DEBUG_DIR", BASE_DIR / "debug"))
    RATE_LIMIT_RPS: float = float(os.getenv("RATE_LIMIT_RPS", "2.0"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))

    def __init__(self) -> None:
        for d in [self.CACHE_DIR, self.OUTPUT_DIR, self.DEBUG_DIR]:
            d.mkdir(parents=True, exist_ok=True)


settings = Settings()
