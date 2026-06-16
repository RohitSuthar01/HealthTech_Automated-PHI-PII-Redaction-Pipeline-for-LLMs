import os
import redis
import logging

logger = logging.getLogger(__name__)


class RedisClient:
    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        db: int | None = None,
        password: str | None = None,
        ssl: bool | None = None,
    ):
        """
        Initializes the Redis connection pool.
        Values default to environment variables when present.
        Supports optional TLS (rediss) via `REDIS_TLS=true`.
        """
        # Load from environment when values are not explicitly provided
        self.host = host or os.getenv("REDIS_HOST", "localhost")
        self.port = int(port or os.getenv("REDIS_PORT", 6379))
        self.db = int(db or os.getenv("REDIS_DB", 0))
        self.password = password or os.getenv("REDIS_PASSWORD")
        env_ssl = os.getenv("REDIS_TLS")
        self.ssl = bool(ssl if ssl is not None else (str(env_ssl).lower() in ("1", "true", "yes")))

        # Build connection pool
        try:
            self.pool = redis.ConnectionPool(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
                ssl=self.ssl,
            )
            self.client = redis.Redis(connection_pool=self.pool)
        except Exception as e:
            logger.exception("Failed to create Redis connection pool: %s", e)
            raise

    def get_client(self) -> redis.Redis:
        """Returns the Redis client instance."""
        return self.client

    def ping(self) -> bool:
        """Tests the connection to the Redis server."""
        try:
            return self.client.ping()
        except redis.ConnectionError as e:
            logger.error("Redis connection failed: %s", e)
            return False
