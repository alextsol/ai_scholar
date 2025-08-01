from dataclasses import dataclass
from typing import Optional, List

@dataclass
class SearchRequest:
    """Data model for search requests"""
    
    query: str
    limit: int = 50
    ai_result_limit: int = 50
    ranking_mode: str = "ai_ranking"
    min_year: Optional[int] = None
    max_year: Optional[int] = None
    backends: Optional[List[str]] = None
    
    def __post_init__(self):
        """Validate and normalize request data"""
        # Normalize query
        self.query = self.query.strip()
        if len(self.query) == 0:
            raise ValueError("Query cannot be empty")
        
        # Validate limits
        if self.limit <= 0:
            raise ValueError("Limit must be positive")
        if self.ai_result_limit <= 0:
            raise ValueError("AI result limit must be positive")
            
        # Validate ranking mode
        valid_modes = ["ai_ranking", "citation_ranking"]
        if self.ranking_mode not in valid_modes:
            raise ValueError(f"Ranking mode must be one of: {valid_modes}")
        
        # Validate years
        if self.min_year and self.min_year < 1900:
            raise ValueError("Minimum year must be >= 1900")
        if self.max_year and self.max_year > 2030:
            raise ValueError("Maximum year must be <= 2030")
        if self.min_year and self.max_year and self.min_year > self.max_year:
            raise ValueError("Minimum year cannot be greater than maximum year")
    
    def to_cache_key(self) -> str:
        """Generate a cache key for this request"""
        backends_str = ",".join(sorted(self.backends)) if self.backends else "all"
        return f"search:{hash(self.query)}:{self.limit}:{self.ai_result_limit}:{self.ranking_mode}:{self.min_year}:{self.max_year}:{backends_str}"
