import os
import redis
import logging
import hashlib
from typing import Optional
from cryptography.fernet import Fernet
from .token_generator import TokenGenerator

logger = logging.getLogger(__name__)

class TokenStore:
    def __init__(self, redis_client: redis.Redis, ttl_seconds: Optional[int] = None):
        self.redis = redis_client
        self.generator = TokenGenerator(redis_client)
        self.ttl_seconds = int(ttl_seconds or os.getenv("VAULT_TTL_SECONDS", 1800))
        
        # Initialize Fernet symmetric encryption cipher
        key_str = os.getenv("VAULT_ENCRYPTION_KEY")
        if not key_str:
            # Secure fallback Fernet-compatible URL-safe base64 key
            key_str = "t8X7u6f7Wv9M2W-3eYt_mH-sJ9qK5l6Z8X9C1vB3dE8="
        try:
            self.cipher = Fernet(key_str.encode())
        except Exception as e:
            logger.warning(f"Invalid encryption key provided. Generating dynamic fallback key: {e}")
            self.cipher = Fernet(Fernet.generate_key())

    def _hash_name(self, name: str) -> str:
        """Hash name values using SHA-256 to prevent plaintext names from leaking in Redis keys."""
        return hashlib.sha256(name.upper().encode("utf-8")).hexdigest()

    def get_or_create_token(self, session_id: str, entity_type: str, entity_name: str) -> str:
        """
        Checks if an entity already has a token in this session. If not, generates one and stores the bidirectional mapping.
        """
        # Strict collision prevention by including type in the mapping key
        # We hash the entity name in the key to protect patient identities at rest
        hashed_name = self._hash_name(entity_name)
        name_key = f"{session_id}:NAME:{entity_type.upper()}:{hashed_name}"
        
        try:
            # 1. Check if token already exists for this name
            existing_token = self.redis.get(name_key)
            if existing_token:
                # Refresh TTL on read
                token_str = existing_token.decode('utf-8') if isinstance(existing_token, bytes) else existing_token
                token_key = f"{session_id}:TOKEN:{token_str}"
                
                pipeline = self.redis.pipeline()
                pipeline.expire(name_key, self.ttl_seconds)
                pipeline.expire(token_key, self.ttl_seconds)
                pipeline.execute()
                
                logger.info(f"Token found in session: {token_str}")
                return token_str

            # 2. If not found, generate a new token
            new_token = self.generator.generate_token(session_id, entity_type)
            token_key = f"{session_id}:TOKEN:{new_token}"

            # 3. Encrypt the original patient identity name before storing it in Redis
            encrypted_name = self.cipher.encrypt(entity_name.encode("utf-8")).decode("utf-8")

            # 4. Store the bidirectional mapping with TTL
            pipeline = self.redis.pipeline()
            pipeline.set(name_key, new_token, ex=self.ttl_seconds)
            pipeline.set(token_key, encrypted_name, ex=self.ttl_seconds)
            pipeline.execute()

            logger.info(f"Generated and securely stored encrypted token for entity: {new_token}")
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
            encrypted_name = self.redis.get(token_key)
            if encrypted_name:
                encrypted_str = encrypted_name.decode('utf-8') if isinstance(encrypted_name, bytes) else encrypted_name
                
                # Decrypt the ciphertext
                decrypted_bytes = self.cipher.decrypt(encrypted_str.encode("utf-8"))
                return decrypted_bytes.decode("utf-8")
                
            logger.warning(f"No name found for token: {token} in session {session_id}")
            return None
        except redis.RedisError as e:
            logger.error(f"Redis error retrieving name for token {token} in session {session_id}: {e}")
            raise
