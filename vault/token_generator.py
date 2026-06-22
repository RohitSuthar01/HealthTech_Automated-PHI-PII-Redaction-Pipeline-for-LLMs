import redis
import logging

logger = logging.getLogger(__name__)

class TokenGenerator:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def generate_token(self, session_id: str, entity_type: str) -> str:
        """
        Generates a sequential token for a given entity type (e.g., PATIENT_001),
        scoped to a specific session to avoid global collisions.
        Uses Redis INCR to ensure atomic, thread-safe counter increments.
        """
        counter_key = f"{session_id}:COUNTER:{entity_type.upper()}"
        try:
            # INCR creates the key if it doesn't exist and increments it by 1 atomically.
            current_count = self.redis.incr(counter_key)
            # Format the token with leading zeros (e.g., 001)
            token = f"{entity_type.upper()}_{current_count:03d}"
            return token
        except redis.RedisError as e:
            logger.error(f"Failed to generate token for {entity_type} in session {session_id}: {e}")
            raise
