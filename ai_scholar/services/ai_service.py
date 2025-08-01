from typing import List, Dict, Any, Optional
from ..interfaces.ai_interface import IAIProvider

class AIService:
    """Service for handling AI-related operations"""
    
    def __init__(self, ai_provider: IAIProvider):
        self.ai_provider = ai_provider
    
    def rank_papers(self, query: str, papers: List[Dict[str, Any]], 
                   ranking_mode: str = 'ai', limit: int = 10) -> List[Dict[str, Any]]:
        """
        Rank papers using AI or other ranking methods
        
        Args:
            query: Original search query
            papers: List of papers to rank
            ranking_mode: Type of ranking ('ai', 'citations', 'year')
            limit: Maximum number of results to return
            
        Returns:
            List of ranked papers with explanations
        """
        if ranking_mode == 'ai' and self.ai_provider:
            return self.ai_provider.rank_papers(query, papers, limit)
        elif ranking_mode == 'citations':
            return self._rank_by_citations(papers, limit)
        elif ranking_mode == 'year':
            return self._rank_by_year(papers, limit)
        else:
            return papers[:limit]
    
    def generate_summary(self, papers: List[Dict[str, Any]], query: str) -> str:
        """Generate a summary of the paper search results"""
        if not self.ai_provider:
            return "AI provider not available for summary generation"
        
        try:
            return self.ai_provider.generate_summary(papers, query)
        except Exception as e:
            return f"Failed to generate summary: {str(e)}"
    
    def generate_research_insights(self, papers: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """Generate research insights from papers"""
        if not self.ai_provider:
            return {"error": "AI provider not available"}
        
        try:
            return self.ai_provider.generate_insights(papers, query)
        except Exception as e:
            return {"error": f"Failed to generate insights: {str(e)}"}
    
    def _rank_by_citations(self, papers: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        """Rank papers by citation count"""
        def get_citations(paper):
            citations = paper.get('citations') or paper.get('citation') or 0
            try:
                return int(citations) if citations != 'N/A' else 0
            except (ValueError, TypeError):
                return 0
        
        sorted_papers = sorted(papers, key=get_citations, reverse=True)
        
        # Add ranking explanation
        for i, paper in enumerate(sorted_papers[:limit]):
            paper['explanation'] = f"Ranked #{i+1} by citations: {paper.get('citations', 'N/A')} citations"
        
        return sorted_papers[:limit]
    
    def _rank_by_year(self, papers: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        """Rank papers by publication year (newest first)"""
        def get_year(paper):
            year = paper.get('year', 0)
            try:
                return int(year) if year != 'Unknown year' else 0
            except (ValueError, TypeError):
                return 0
        
        sorted_papers = sorted(papers, key=get_year, reverse=True)
        
        # Add ranking explanation
        for i, paper in enumerate(sorted_papers[:limit]):
            paper['explanation'] = f"Ranked #{i+1} by year: {paper.get('year', 'Unknown')} publication year"
        
        return sorted_papers[:limit]
