"""
Redis client for caching.
Provides connection management and caching utilities.
"""

import json
import logging
from typing import Any, Optional
from urllib.parse import urlparse

import redis
from redis.connection import ConnectionPool

from api.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Redis client wrapper with caching utilities.
    """

    def __init__(
        self,
        url: Optional[str] = None,
        max_connections: Optional[int] = None,
        socket_timeout: Optional[int] = None,
        socket_connect_timeout: Optional[int] = None,
    ):
        """
        Initialize Redis client.
        
        Args:
            url: Redis connection URL (default from settings)
            max_connections: Max connections in pool (default from settings)
            socket_timeout: Socket timeout in seconds (default from settings)
            socket_connect_timeout: Socket connect timeout (default from settings)
        """
        self.url = url or settings.redis_url
        self.max_connections = max_connections or settings.redis_max_connections
        self.socket_timeout = socket_timeout or settings.redis_socket_timeout
        self.socket_connect_timeout = (
            socket_connect_timeout or settings.redis_socket_connect_timeout
        )
        
        # Parse Redis URL
        parsed = urlparse(self.url)
        
        # Create connection pool
        self.pool = ConnectionPool(
            host=parsed.hostname or "localhost",
            port=parsed.port or 6379,
            db=int(parsed.path[1:]) if parsed.path else 0,
            password=parsed.password,
            max_connections=self.max_connections,
            socket_timeout=self.socket_timeout,
            socket_connect_timeout=self.socket_connect_timeout,
            decode_responses=True,  # Decode bytes to strings
        )
        
        # Create Redis client
        self.client = redis.Redis(connection_pool=self.pool)
        
        logger.info(f"Redis client initialized: {parsed.hostname}:{parsed.port}")

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except redis.RedisError as e:
            logger.error(f"Redis GET error for key {key}: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for key {key}: {str(e)}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            serialized = json.dumps(value)
            if ttl:
                return self.client.setex(key, ttl, serialized)
            else:
                return self.client.set(key, serialized)
        except redis.RedisError as e:
            logger.error(f"Redis SET error for key {key}: {str(e)}")
            return False
        except (TypeError, ValueError) as e:
            logger.error(f"JSON encode error for key {key}: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            return bool(self.client.delete(key))
        except redis.RedisError as e:
            logger.error(f"Redis DELETE error for key {key}: {str(e)}")
            return False

    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if exists, False otherwise
        """
        try:
            return bool(self.client.exists(key))
        except redis.RedisError as e:
            logger.error(f"Redis EXISTS error for key {key}: {str(e)}")
            return False

    def ttl(self, key: str) -> int:
        """
        Get remaining time to live for key.
        
        Args:
            key: Cache key
            
        Returns:
            Seconds until expiry, -1 if no expiry, -2 if doesn't exist
        """
        try:
            return self.client.ttl(key)
        except redis.RedisError as e:
            logger.error(f"Redis TTL error for key {key}: {str(e)}")
            return -2

    def flush(self) -> bool:
        """
        Flush all keys in current database.
        WARNING: This deletes all cached data!
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.warning("Flushing all Redis keys in current database")
            return self.client.flushdb()
        except redis.RedisError as e:
            logger.error(f"Redis FLUSHDB error: {str(e)}")
            return False

    def get_stats(self) -> dict:
        """
        Get Redis statistics.
        
        Returns:
            Dictionary with Redis stats
        """
        try:
            info = self.client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "total_connections_received": info.get("total_connections_received", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0),
                ),
            }
        except redis.RedisError as e:
            logger.error(f"Redis INFO error: {str(e)}")
            return {}

    def check_connection(self) -> bool:
        """
        Check if Redis connection is working.
        
        Returns:
            True if connected, False otherwise
        """
        try:
            self.client.ping()
            logger.info("Redis connection OK")
            return True
        except redis.RedisError as e:
            logger.error(f"Redis connection failed: {str(e)}")
            return False

    @staticmethod
    def _calculate_hit_rate(hits: int, misses: int) -> float:
        """Calculate cache hit rate."""
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0.0

    def close(self):
        """Close Redis connection pool."""
        self.pool.disconnect()
        logger.info("Redis connection pool closed")


# Singleton instance
_redis_client: Optional[RedisClient] = None


def get_redis_client() -> RedisClient:
    """
    Get singleton Redis client instance.
    
    Returns:
        Redis client instance
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client


def get_redis() -> RedisClient:
    """
    Dependency injection for Redis client.
    
    Usage:
        @app.get("/items")
        def read_items(redis: RedisClient = Depends(get_redis)):
            return redis.get("items")
    """
    return get_redis_client()