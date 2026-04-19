from dataclasses import dataclass, field
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    # Browser
    headless: bool = field(default_factory=lambda: os.getenv("HEADLESS", "false").lower() == "true")
    timeout: int = field(default_factory=lambda: int(os.getenv("TIMEOUT", "30000")))

    # Cache
    cache_enabled: bool = field(default_factory=lambda: os.getenv("CACHE_ENABLED", "true").lower() == "true")
    cache_ttl: int = field(default_factory=lambda: int(os.getenv("CACHE_TTL", "3600")))
    cache_dir: Path = field(default_factory=lambda: Path(os.getenv("CACHE_DIR", ".cache")))

    # Rate limiting
    rate_limit_requests: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_REQUESTS", "5")))
    rate_limit_window: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_WINDOW", "60")))

    # Retry
    max_retries: int = field(default_factory=lambda: int(os.getenv("MAX_RETRIES", "3")))
    retry_delay: float = field(default_factory=lambda: float(os.getenv("RETRY_DELAY", "1.0")))

    # Logging — WARNING by default so library internals don't pollute user output
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "WARNING"))

    # Proxy
    proxy_url: str = field(default_factory=lambda: os.getenv("PROXY_URL", ""))

    def __post_init__(self):
        self.cache_dir.mkdir(parents=True, exist_ok=True)


config = Config()
