import logging
from vault.redis_client import RedisClient

# Configure basic logging to see the output in the console
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_redis_connection():
    """
    Day 2 Task: Verify Python can connect to the local Redis server.
    """
    print("--- Starting Redis Connection Test ---")

    # Initialize the client. This connects to localhost:6379 by default.
    # Ensure your local Redis server is running!
    client = RedisClient()
    
    # Ping the server to verify the connection
    is_connected = client.ping()
    
    if is_connected:
        print("\n✅ SUCCESS: Successfully connected to Redis!")
        print("Your Python environment is ready for the Vault engine.")
    else:
        print("\n❌ FAILED: Could not connect to Redis.")
        print("Please ensure your Redis server is running on localhost port 6379.")

if __name__ == "__main__":
    test_redis_connection()
