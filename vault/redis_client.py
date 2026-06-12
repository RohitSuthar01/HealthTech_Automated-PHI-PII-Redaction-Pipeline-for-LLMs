import redis
import logging

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0, password: str = None):
        """
        Initializes the Redis connection pool.
        In a production environment, host, port, and password should be loaded from environment variables.
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.pool = redis.ConnectionPool(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            decode_responses=True # Automatically decodes byte responses to strings
        )
        self.client = redis.Redis(connection_pool=self.pool)

    def get_client(self) -> redis.Redis:
        """Returns the Redis client instance."""
        return self.client

    def ping(self) -> bool:
        """Tests the connection to the Redis server."""
        try:
            return self.client.ping()
        except redis.ConnectionError as e:
            logger.error(f"Redis connection failed: {e}")
            return False
