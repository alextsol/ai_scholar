from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from .paper import Paper

@dataclass
class SearchResult:
    """Data model for search results"""
    
    papers: List[Paper]
    query: str
    total_found: int
    processing_time: float
    ranking_mode: str
    backends_used: List[str]
    ai_provider_used: Optional[str] = None
    cache_hit: bool = False
    created_at: Optional[datetime] = None
    
    # Aggregation statistics for transparency
    aggregation_stats: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Set creation timestamp"""
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert search result to dictionary"""
        return {
            "papers": [paper.to_dict() for paper in self.papers],
            "query": self.query,
            "total_found": self.total_found,
            "processing_time": self.processing_time,
            "ranking_mode": self.ranking_mode,
            "backends_used": self.backends_used,
            "ai_provider_used": self.ai_provider_used,
            "cache_hit": self.cache_hit,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "aggregation_stats": self.aggregation_stats
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchResult':
        """Create search result from dictionary"""
        papers = [Paper.from_dict(paper_data) for paper_data in data.get('papers', [])]
        created_at = None
        
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])
            
        return cls(
            papers=papers,
            query=data.get('query', ''),
            total_found=data.get('total_found', 0),
            processing_time=data.get('processing_time', 0.0),
            ranking_mode=data.get('ranking_mode', 'ai_ranking'),
            backends_used=data.get('backends_used', []),
            ai_provider_used=data.get('ai_provider_used'),
            cache_hit=data.get('cache_hit', False),
            created_at=created_at,
            aggregation_stats=data.get('aggregation_stats')
        )
