from abc import ABC, abstractmethod
from typing import Any, Optional

class ICacheProvider(ABC):
    """Abstract interface for cache providers"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Store a value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None = no expiry)
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Delete a value from cache
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """
        Clear all cached values
        
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def cleanup_expired(self) -> int:
        """
        Remove expired cache entries
        
        Returns:
            Number of entries removed
        """
        pass
