import os
import time
import logging
import functools
from typing import Optional, List, Dict, Any, Tuple
import redis

from .token_store import TokenStore
from .nlp_adapter import NLPAdapter
from .text_engine import TextEngine
from .exceptions import VaultError

logger = logging.getLogger(__name__)

def track_latency(func):
    """Decorator to measure execution time of Vault operations for latency tracking."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.info(f"Vault.{func.__name__} completed in {elapsed_ms:.2f} ms")
    return wrapper

class Vault:
    """
    High-level Vault Engine facade integrating Token Storage, NLP processing, and Text Redaction.
    Provides session-scoped, secure pseudonymization for clinical notes.
    """

    def __init__(self, redis_client: redis.Redis, ttl_seconds: Optional[int] = None):
        self.redis = redis_client
        self.token_store = TokenStore(redis_client, ttl_seconds)
        self.nlp_adapter = NLPAdapter(self.token_store)

    @track_latency
    def redact_note(self, session_id: str, text: str, nlp_entities: List[Dict[str, Any]], confidence_threshold: float = 0.7) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Redacts sensitive entities in the provided text using the given NLP outputs.
        Returns a tuple of (redacted_text, processed_entities_with_tokens).
        """
        try:
            # 1. Process NLP entities to generate or retrieve tokens
            processed_entities = self.nlp_adapter.process_entities(session_id, nlp_entities, threshold=confidence_threshold)
            
            # 2. Perform text replacement
            redacted_text = TextEngine.redact(text, processed_entities)
            
            return redacted_text, processed_entities
        except Exception as e:
            logger.exception(f"Redaction failed for session {session_id}: {e}")
            raise VaultError(f"Failed to redact note: {str(e)}") from e

    @track_latency
    def restore_note(self, session_id: str, redacted_text: str) -> str:
        """
        Restores a redacted note back to its original form using tokens stored in the session.
        """
        try:
            restored_text = TextEngine.restore(session_id, redacted_text, self.token_store)
            return restored_text
        except Exception as e:
            logger.exception(f"Restoration failed for session {session_id}: {e}")
            raise VaultError(f"Failed to restore note: {str(e)}") from e

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
            raise VaultError(f"Failed to clear session: {str(e)}") from e
