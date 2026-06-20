import os
import logging
from typing import Optional
import redis

logger = logging.getLogger(__name__)


class Vault:
    """High-level Vault wrapper for storing reversible PHI token mappings in Redis.

    Responsibilities:
    - store mappings with mandatory TTL
    - retrieve original values
    - refresh TTL for all keys in a session
    - clear session keys
    """

    def __init__(self, redis_client: redis.Redis, ttl_seconds: Optional[int] = None):
        self.redis = redis_client
        self.ttl_seconds = int(ttl_seconds or os.getenv("VAULT_TTL_SECONDS", 1800))

    def _key(self, session_id: str, entity_type: str, token: str) -> str:
        return f"{session_id}:{entity_type.upper()}:{token.upper()}"

    def store_mapping(self, session_id: str, entity_type: str, token: str, original_value: str) -> None:
        """Store a mapping with configured TTL. Does NOT log the original value."""
        key = self._key(session_id, entity_type, token)
        try:
            # Use EX to set TTL atomically with the value
            self.redis.set(key, original_value, ex=self.ttl_seconds)
            logger.info("Vault store", extra={"session_id": session_id, "entity_type": entity_type, "token": token})
        except redis.RedisError as e:
            logger.exception("Failed to store mapping in vault: %s", e)
            raise

    def get_original_value(self, session_id: str, entity_type: str, token: str) -> Optional[str]:
        key = self._key(session_id, entity_type, token)
        try:
            return self.redis.get(key)
        except redis.RedisError as e:
            logger.exception("Failed to retrieve mapping from vault: %s", e)
            raise

    def refresh_session_ttl(self, session_id: str, ttl_seconds: Optional[int] = None) -> int:
        """Extend TTL on all keys belonging to a session. Returns number of keys updated."""
        ttl = int(ttl_seconds or self.ttl_seconds)
        pattern = f"{session_id}:*"
        try:
            keys = self.redis.keys(pattern)
            if not keys:
                return 0
            pipe = self.redis.pipeline()
            for key in keys:
                pipe.expire(key, ttl)
            pipe.execute()
            return len(keys)
        except redis.RedisError as e:
            logger.exception("Failed to refresh TTL for session %s: %s", session_id, e)
            raise

    def clear_session(self, session_id: str) -> int:
        """Delete all vault keys for a session. Returns count of keys removed."""
        pattern = f"{session_id}:*"
        try:
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
            return 0
        except redis.RedisError as e:
            logger.exception("Failed to clear session %s: %s", session_id, e)
            raise
