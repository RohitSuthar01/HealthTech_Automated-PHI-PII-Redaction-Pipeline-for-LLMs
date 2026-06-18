"""
vault.py
--------
Stores reversible pseudonym → real-identity token maps per session.
Backed by Redis with TTL. Falls back to in-memory dict if Redis
is unavailable (useful for local dev without Redis installed).
"""

import json
import time
import os

try:
    import redis
    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False

DEFAULT_TTL = int(os.getenv("VAULT_TTL_SECONDS", 1800))  # 30 min


# ─────────────────────────────────────────────
# In-memory fallback (no Redis needed for demo)
# ─────────────────────────────────────────────
class _InMemoryStore:
    def __init__(self):
        self._data = {}

    def set(self, key, value, ex=None):
        expires = time.time() + ex if ex else None
        self._data[key] = (value, expires)

    def get(self, key):
        entry = self._data.get(key)
        if not entry:
            return None
        value, expires = entry
        if expires and time.time() > expires:
            del self._data[key]
            return None
        return value

    def delete(self, key):
        self._data.pop(key, None)

    def keys(self, pattern="*"):
        # naive pattern match for phi-vault:* only
        prefix = pattern.replace("*", "")
        return [k for k in self._data if k.startswith(prefix)]


# ─────────────────────────────────────────────
# Vault
# ─────────────────────────────────────────────
class Vault:
    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.ttl  = DEFAULT_TTL

        if _REDIS_AVAILABLE:
            try:
                self._client = redis.Redis.from_url(redis_url, decode_responses=True)
                self._client.ping()
                print("✅ Vault: connected to Redis")
            except Exception:
                print("⚠️  Vault: Redis unavailable, using in-memory store")
                self._client = _InMemoryStore()
        else:
            print("⚠️  Vault: redis-py not installed, using in-memory store")
            self._client = _InMemoryStore()

    def store(self, session_id, token_map):
        key = f"phi-vault:{session_id}"
        self._client.set(key, json.dumps(token_map), ex=self.ttl)

    def get(self, session_id):
        key = f"phi-vault:{session_id}"
        raw = self._client.get(key)
        return json.loads(raw) if raw else {}

    def delete(self, session_id):
        self._client.delete(f"phi-vault:{session_id}")

    def all_sessions(self):
        keys = self._client.keys("phi-vault:*")
        return [k.replace("phi-vault:", "") for k in keys]


# Singleton — imported by routes
vault = Vault()
