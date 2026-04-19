import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Any
from intelliscraper.utils.logger import get_logger

logger = get_logger(__name__)


class CacheEntry:
    def __init__(self, url: str, content: str, ttl: int):
        self.url = url
        self.content = content
        self.timestamp = datetime.now()
        self.ttl = ttl

    @property
    def is_expired(self) -> bool:
        return (datetime.now() - self.timestamp).total_seconds() > self.ttl

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "ttl": self.ttl
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CacheEntry":
        entry = cls(data["url"], data["content"], data["ttl"])
        entry.timestamp = datetime.fromisoformat(data["timestamp"])
        return entry


class Cache:
    def __init__(self, cache_dir: Path = Path(".cache"), ttl: int = 3600, enabled: bool = True):
        self.cache_dir = cache_dir
        self.ttl = ttl
        self.enabled = enabled
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, key: str) -> Path:
        hash_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{hash_key}.json"

    def get(self, key: str) -> Optional[str]:
        if not self.enabled:
            return None

        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            return None

        try:
            with open(cache_path) as f:
                entry = CacheEntry.from_dict(json.load(f))
            
            if entry.is_expired:
                cache_path.unlink()
                return None
            
            logger.debug(f"Cache hit for {key}")
            return entry.content
        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            logger.debug(f"Cache error for {key}: {e}")
            return None

    def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        if not self.enabled:
            return

        entry = CacheEntry(key, value, ttl or self.ttl)
        cache_path = self._get_cache_path(key)

        try:
            with open(cache_path, "w") as f:
                json.dump(entry.to_dict(), f)
            logger.debug(f"Cached {key}")
        except IOError as e:
            logger.warning(f"Failed to cache {key}: {e}")

    def delete(self, key: str) -> bool:
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            cache_path.unlink()
            return True
        return False

    def clear(self) -> int:
        count = sum(1 for f in self.cache_dir.glob("*.json") if f.unlink() is None)
        logger.info(f"Cleared {count} cache entries")
        return count

    def cleanup_expired(self) -> int:
        expired_count = 0
        for file in self.cache_dir.glob("*.json"):
            try:
                with open(file) as f:
                    entry = CacheEntry.from_dict(json.load(f))
                if entry.is_expired:
                    file.unlink()
                    expired_count += 1
            except (json.JSONDecodeError, FileNotFoundError, KeyError):
                file.unlink()
                expired_count += 1
        
        logger.info(f"Cleaned up {expired_count} expired entries")
        return expired_count

    def get_stats(self) -> dict:
        files = list(self.cache_dir.glob("*.json"))
        return {
            "total_entries": len(files),
            "cache_dir": str(self.cache_dir),
            "enabled": self.enabled
        }


cache = Cache()
