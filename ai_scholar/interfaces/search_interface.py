from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class ISearchProvider(ABC):
    """Abstract interface for search providers (arXiv, Semantic Scholar, etc.)"""
    
    @abstractmethod
    def search(self, query: str, limit: int, min_year: Optional[int] = None, max_year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search for papers using the provider's API
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            min_year: Minimum publication year filter
            max_year: Maximum publication year filter
            
        Returns:
            List of paper dictionaries with standardized fields
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the name of this search provider"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is currently available"""
        pass
    
    def validate_query(self, query: str) -> bool:
        """Validate if the query is acceptable for this provider"""
        return len(query.strip()) > 0
