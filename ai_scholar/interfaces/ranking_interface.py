from abc import ABC, abstractmethod
from typing import List, Dict, Any

class IRankingProvider(ABC):
    """Abstract interface for paper ranking providers"""
    
    @abstractmethod
    def rank_papers(self, query: str, papers: List[Dict[str, Any]], ranking_mode: str = "ai_ranking") -> List[Dict[str, Any]]:
        """
        Rank papers based on relevance to query
        
        Args:
            query: Search query
            papers: List of papers to rank
            ranking_mode: Ranking algorithm to use
            
        Returns:
            List of ranked papers with scores and explanations
        """
        pass
    
    @abstractmethod
    def generate_explanations(self, query: str, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate explanations for why papers are relevant
        
        Args:
            query: Search query
            papers: List of papers needing explanations
            
        Returns:
            List of papers with explanations added
        """
        pass
    
    @abstractmethod
    def get_ranking_algorithm_name(self) -> str:
        """Return the name of this ranking algorithm"""
        pass
    
    @abstractmethod
    def supports_mode(self, ranking_mode: str) -> bool:
        """Check if this provider supports the given ranking mode"""
        pass
