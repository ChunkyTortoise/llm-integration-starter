"""In-memory LRU cache with TTL."""
from __future__ import annotations

import hashlib
import json
import time
from collections import OrderedDict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

class LRUCache:
    def __init__(self, max_size: int = 100, ttl_seconds: float = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict = OrderedDict()
        self._hits = 0
        self._misses = 0

    def get(self, key: str):
        if key not in self._cache:
            self._misses += 1
            return None
        response, timestamp = self._cache[key]
        age = time.time() - timestamp
        if age > self.ttl_seconds:
            del self._cache[key]
            self._misses += 1
            return None
        self._cache.move_to_end(key)
        self._hits += 1
        return response

    def put(self, key: str, value) -> None:
        if key in self._cache:
            self._cache[key] = (value, time.time())
            self._cache.move_to_end(key)
            return
        self._cache[key] = (value, time.time())
        if len(self._cache) > self.max_size:
            self._cache.popitem(last=False)

    def make_key(self, provider: str, model: str, messages: list[dict], temperature: float = 0.0) -> str:
        key_data = {"provider": provider, "model": model, "messages": messages, "temperature": temperature}
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def clear(self) -> None:
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    @property
    def size(self) -> int:
        return len(self._cache)

    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses
        if total == 0:
            return 0.0
        return (self._hits / total) * 100.0

    @property
    def stats(self) -> dict:
        return {
            "hits": self._hits,
            "misses": self._misses,
            "size": self.size,
            "max_size": self.max_size,
            "hit_rate": self.hit_rate,
        }
