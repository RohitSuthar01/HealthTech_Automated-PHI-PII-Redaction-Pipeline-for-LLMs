import os
import redis
import logging
from typing import Optional
from .token_generator import TokenGenerator

logger = logging.getLogger(__name__)

class TokenStore:
    def __init__(self, redis_client: redis.Redis, ttl_seconds: Optional[int] = None):
        self.redis = redis_client
        self.generator = TokenGenerator(redis_client)
        self.ttl_seconds = int(ttl_seconds or os.getenv("VAULT_TTL_SECONDS", 1800))

    def get_or_create_token(self, session_id: str, entity_type: str, entity_name: str) -> str:
        """
        Checks if an entity already has a token in this session. If not, generates one and stores the bidirectional mapping.
        """
        # Strict collision prevention by including type in the mapping key
        name_key = f"{session_id}:NAME:{entity_type.upper()}:{entity_name.upper()}"
        
        try:
            # 1. Check if token already exists for this name
            existing_token = self.redis.get(name_key)
            if existing_token:
                # Refresh TTL on read
                token_key = f"{session_id}:TOKEN:{existing_token.decode('utf-8') if isinstance(existing_token, bytes) else existing_token}"
                pipeline = self.redis.pipeline()
                pipeline.expire(name_key, self.ttl_seconds)
                pipeline.expire(token_key, self.ttl_seconds)
                pipeline.execute()
                
                token_str = existing_token.decode('utf-8') if isinstance(existing_token, bytes) else existing_token
                logger.info(f"Token found for {entity_name}: {token_str}")
                return token_str

            # 2. If not found, generate a new token
            new_token = self.generator.generate_token(session_id, entity_type)
            token_key = f"{session_id}:TOKEN:{new_token}"

            # 3. Store the bidirectional mapping with TTL
            # We use a pipeline to ensure both keys are set atomically with TTLs
            pipeline = self.redis.pipeline()
            pipeline.set(name_key, new_token, ex=self.ttl_seconds)
            pipeline.set(token_key, entity_name, ex=self.ttl_seconds)
            pipeline.execute()

            logger.info(f"Generated and stored new token for {entity_name}: {new_token}")
            return new_token

        except redis.RedisError as e:
            logger.error(f"Redis error during token operation for {entity_name}: {e}")
            raise

    def get_name_from_token(self, session_id: str, token: str) -> Optional[str]:
        """
        Retrieves the original entity name from a given token within a session. Used for reversing pseudonymization.
        """
        token_key = f"{session_id}:TOKEN:{token.upper()}"
        try:
            name = self.redis.get(token_key)
            if name:
                name_str = name.decode('utf-8') if isinstance(name, bytes) else name
                return name_str
            logger.warning(f"No name found for token: {token} in session {session_id}")
            return None
        except redis.RedisError as e:
            logger.error(f"Redis error retrieving name for token {token} in session {session_id}: {e}")
            raise

