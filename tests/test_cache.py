"""Tests for LRU cache."""

from __future__ import annotations

import time

from llm_integration_starter.cache import LRUCache


class TestLRUCache:
    """Tests for LRUCache."""

    def test_cache_initialization(self):
        """Test creating a cache."""
        cache = LRUCache(max_size=100, ttl_seconds=3600)
        assert cache.max_size == 100
        assert cache.ttl_seconds == 3600
        assert cache.size == 0

    def test_cache_put_and_get(self, sample_response):
        """Test putting and getting from cache."""
        cache = LRUCache()
        key = "test_key"

        cache.put(key, sample_response)
        result = cache.get(key)

        assert result is not None
        assert result.text == sample_response.text

    def test_cache_miss_returns_none(self):
        """Test cache miss returns None."""
        cache = LRUCache()
        result = cache.get("nonexistent_key")
        assert result is None

    def test_cache_make_key(self):
        """Test generating cache keys."""
        cache = LRUCache()
        messages = [{"role": "user", "content": "Hello"}]

        key1 = cache.make_key("claude", "model-1", messages, 0.7)
        key2 = cache.make_key("claude", "model-1", messages, 0.7)
        key3 = cache.make_key("openai", "model-1", messages, 0.7)

        # Same parameters should produce same key
        assert key1 == key2
        # Different provider should produce different key
        assert key1 != key3

    def test_cache_ttl_expiration(self, sample_response):
        """Test cache entries expire after TTL."""
        cache = LRUCache(ttl_seconds=0.1)
        key = "test_key"

        cache.put(key, sample_response)
        assert cache.get(key) is not None

        # Wait for TTL to expire
        time.sleep(0.2)
        assert cache.get(key) is None

    def test_cache_lru_eviction(self, sample_response):
        """Test least recently used items are evicted."""
        cache = LRUCache(max_size=2)

        cache.put("key1", sample_response)
        cache.put("key2", sample_response)
        cache.put("key3", sample_response)  # Should evict key1

        assert cache.get("key1") is None  # Evicted
        assert cache.get("key2") is not None
        assert cache.get("key3") is not None

    def test_cache_hit_rate(self, sample_response):
        """Test cache hit rate calculation."""
        cache = LRUCache()
        cache.put("key1", sample_response)

        # Miss
        cache.get("nonexistent")
        assert cache.hit_rate == 0.0

        # Hit
        cache.get("key1")
        assert cache.hit_rate == 50.0  # 1 hit, 1 miss

    def test_cache_clear(self, sample_response):
        """Test clearing the cache."""
        cache = LRUCache()
        cache.put("key1", sample_response)
        cache.get("key1")

        cache.clear()

        assert cache.size == 0
        assert cache.hit_rate == 0.0
        assert cache.get("key1") is None

    def test_cache_size_property(self, sample_response):
        """Test cache size property."""
        cache = LRUCache()
        assert cache.size == 0

        cache.put("key1", sample_response)
        assert cache.size == 1

        cache.put("key2", sample_response)
        assert cache.size == 2

    def test_cache_stats(self, sample_response):
        """Test cache statistics."""
        cache = LRUCache(max_size=10)
        cache.put("key1", sample_response)
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss

        stats = cache.stats
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["size"] == 1
        assert stats["max_size"] == 10
        assert stats["hit_rate"] == 50.0

    def test_cache_update_existing_key(self, sample_response):
        """Test updating an existing key in cache."""
        cache = LRUCache()
        cache.put("key1", sample_response)

        # Update with different response
        from llm_integration_starter.client import LLMResponse

        new_response = LLMResponse(
            text="Updated",
            input_tokens=5,
            output_tokens=5,
            cost=0.0001,
            latency_ms=100.0,
            provider="mock",
            model="mock",
        )
        cache.put("key1", new_response)

        result = cache.get("key1")
        assert result.text == "Updated"
        assert cache.size == 1  # Should not increase size
