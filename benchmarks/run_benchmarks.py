"""LLM Integration Starter Performance Benchmarks."""
import time
import random
import hashlib
import json
from pathlib import Path
from collections import deque

random.seed(42)


def percentile(data, p):
    k = (len(data) - 1) * p / 100
    f = int(k)
    c = f + 1 if f + 1 < len(data) else f
    return data[f] + (k - f) * (data[c] - data[f])


# --- Synthetic data ---

CACHE_KEYS = [f"prompt:{hashlib.md5(f'query_{i}'.encode()).hexdigest()}" for i in range(500)]
CACHE_VALUES = [
    json.dumps({
        "response": f"This is a cached LLM response for query {i}. " * 5,
        "model": random.choice(["claude-3", "gpt-4", "gemini-pro"]),
        "tokens": random.randint(50, 500),
        "latency_ms": random.uniform(200, 3000),
        "timestamp": time.time() - random.randint(0, 3600),
    })
    for i in range(500)
]

PROVIDERS = ["claude", "gpt4", "gemini", "mistral", "llama"]


# --- Benchmarks ---

def benchmark_cache_lookup_write():
    """Cache lookup and write operations (dict-based LRU)."""
    # Simple LRU cache implementation
    class LRUCache:
        def __init__(self, capacity=256):
            self.capacity = capacity
            self.cache = {}
            self.order = deque()

        def get(self, key):
            if key in self.cache:
                self.order.remove(key)
                self.order.append(key)
                return self.cache[key]
            return None

        def put(self, key, value):
            if key in self.cache:
                self.order.remove(key)
            elif len(self.cache) >= self.capacity:
                oldest = self.order.popleft()
                del self.cache[oldest]
            self.cache[key] = value
            self.order.append(key)

    times = []
    for _ in range(500):
        cache = LRUCache(256)
        start = time.perf_counter()
        # Write phase
        for i in range(200):
            cache.put(CACHE_KEYS[i], CACHE_VALUES[i])
        # Read phase (mix of hits and misses)
        hits = 0
        for i in range(300):
            key = CACHE_KEYS[i % 500]
            result = cache.get(key)
            if result is not None:
                hits += 1
        # Eviction phase
        for i in range(200, 400):
            cache.put(CACHE_KEYS[i], CACHE_VALUES[i])
        hit_rate = hits / 300
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    times.sort()
    return {
        "op": "LRU Cache Ops (200 write, 300 read, 200 evict)",
        "n": 500,
        "p50": round(percentile(times, 50), 4),
        "p95": round(percentile(times, 95), 4),
        "p99": round(percentile(times, 99), 4),
        "ops_sec": round(500 / (sum(times) / 1000), 1),
    }


def benchmark_circuit_breaker():
    """Circuit breaker state transitions."""
    class CircuitBreaker:
        CLOSED = "closed"
        OPEN = "open"
        HALF_OPEN = "half_open"

        def __init__(self, failure_threshold=5, recovery_timeout=30.0):
            self.state = self.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.failure_threshold = failure_threshold
            self.recovery_timeout = recovery_timeout
            self.last_failure_time = 0.0

        def record_success(self):
            if self.state == self.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= 3:
                    self.state = self.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
            elif self.state == self.CLOSED:
                self.failure_count = max(0, self.failure_count - 1)

        def record_failure(self, current_time):
            self.failure_count += 1
            self.last_failure_time = current_time
            if self.failure_count >= self.failure_threshold:
                self.state = self.OPEN

        def can_execute(self, current_time):
            if self.state == self.CLOSED:
                return True
            if self.state == self.OPEN:
                if current_time - self.last_failure_time >= self.recovery_timeout:
                    self.state = self.HALF_OPEN
                    self.success_count = 0
                    return True
                return False
            return True  # HALF_OPEN allows trial

    # Simulate provider circuit breakers
    events = []
    for _ in range(500):
        provider = random.choice(PROVIDERS)
        success = random.random() > 0.3  # 30% failure rate
        timestamp = time.time() + random.uniform(0, 120)
        events.append((provider, success, timestamp))

    times = []
    for _ in range(1000):
        breakers = {p: CircuitBreaker() for p in PROVIDERS}
        start = time.perf_counter()
        for provider, success, ts in events:
            cb = breakers[provider]
            can_exec = cb.can_execute(ts)
            if can_exec:
                if success:
                    cb.record_success()
                else:
                    cb.record_failure(ts)
        # Collect final states
        states = {p: cb.state for p, cb in breakers.items()}
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    times.sort()
    return {
        "op": "Circuit Breaker (500 events, 5 providers)",
        "n": 1000,
        "p50": round(percentile(times, 50), 4),
        "p95": round(percentile(times, 95), 4),
        "p99": round(percentile(times, 99), 4),
        "ops_sec": round(1000 / (sum(times) / 1000), 1),
    }


def benchmark_fallback_chain():
    """Fallback chain traversal across providers."""
    # Simulate provider availability
    chain_configs = []
    for _ in range(100):
        chain = random.sample(PROVIDERS, k=random.randint(2, 5))
        # Each provider has a simulated availability probability
        avail = {p: random.uniform(0.5, 0.99) for p in chain}
        chain_configs.append((chain, avail))

    times = []
    for _ in range(1000):
        start = time.perf_counter()
        for chain, avail in chain_configs:
            selected = None
            attempts = 0
            latency_total = 0.0
            for provider in chain:
                attempts += 1
                # Simulate health check latency
                check_latency = random.uniform(0.001, 0.01)  # mock
                latency_total += check_latency
                # Deterministic availability check based on hash
                is_available = hash((provider, attempts)) % 100 < avail[provider] * 100
                if is_available:
                    selected = provider
                    break
            result = {
                "provider": selected or "none",
                "attempts": attempts,
                "total_latency": round(latency_total, 4),
                "exhausted": selected is None,
            }
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    times.sort()
    return {
        "op": "Fallback Chain Traversal (100 chains)",
        "n": 1000,
        "p50": round(percentile(times, 50), 4),
        "p95": round(percentile(times, 95), 4),
        "p99": round(percentile(times, 99), 4),
        "ops_sec": round(1000 / (sum(times) / 1000), 1),
    }


def benchmark_batch_queue():
    """Batch queue: enqueue, dequeue, priority sorting."""
    class BatchQueue:
        def __init__(self, max_batch_size=32):
            self.queue = []
            self.max_batch_size = max_batch_size

        def enqueue(self, item, priority=0):
            self.queue.append((priority, item))

        def dequeue_batch(self):
            self.queue.sort(key=lambda x: -x[0])  # High priority first
            batch = self.queue[:self.max_batch_size]
            self.queue = self.queue[self.max_batch_size:]
            return [item for _, item in batch]

        def size(self):
            return len(self.queue)

    items = [
        {"prompt": f"Query {i}", "model": random.choice(PROVIDERS), "tokens": random.randint(10, 200)}
        for i in range(500)
    ]
    priorities = [random.randint(0, 10) for _ in range(500)]

    times = []
    for _ in range(500):
        q = BatchQueue(max_batch_size=32)
        start = time.perf_counter()
        # Enqueue all
        for item, prio in zip(items, priorities):
            q.enqueue(item, prio)
        # Dequeue in batches
        batches = []
        while q.size() > 0:
            batch = q.dequeue_batch()
            # Simulate batch processing: compute total tokens
            total_tokens = sum(it["tokens"] for it in batch)
            batches.append({"size": len(batch), "tokens": total_tokens})
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    times.sort()
    return {
        "op": "Batch Queue (500 items, batch=32)",
        "n": 500,
        "p50": round(percentile(times, 50), 4),
        "p95": round(percentile(times, 95), 4),
        "p99": round(percentile(times, 99), 4),
        "ops_sec": round(500 / (sum(times) / 1000), 1),
    }


def main():
    results = []
    benchmarks = [
        benchmark_cache_lookup_write,
        benchmark_circuit_breaker,
        benchmark_fallback_chain,
        benchmark_batch_queue,
    ]
    for bench in benchmarks:
        print(f"Running {bench.__doc__.strip()}...")
        r = bench()
        results.append(r)
        print(f"  P50: {r['p50']}ms | P95: {r['p95']}ms | P99: {r['p99']}ms | {r['ops_sec']} ops/sec")

    out = Path(__file__).parent / "RESULTS.md"
    with open(out, "w") as f:
        f.write("# LLM Integration Starter Benchmark Results\n\n")
        f.write(f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("| Operation | Iterations | P50 (ms) | P95 (ms) | P99 (ms) | Throughput |\n")
        f.write("|-----------|-----------|----------|----------|----------|------------|\n")
        for r in results:
            f.write(f"| {r['op']} | {r['n']:,} | {r['p50']} | {r['p95']} | {r['p99']} | {r['ops_sec']:,.0f} ops/sec |\n")
        f.write("\n> All benchmarks use synthetic data. No external services required.\n")
    print(f"\nResults: {out}")


if __name__ == "__main__":
    main()
