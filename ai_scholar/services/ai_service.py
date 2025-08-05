from typing import List, Dict, Any, Optional
from ..interfaces.ai_interface import IAIProvider
from ..enums.search_modes import RankingMode

class AIService:
    DEFAULT_LIMIT = 10
    CITATION_NA_VALUE = 'N/A'
    UNKNOWN_YEAR_VALUE = 'Unknown year'
    
    def __init__(self, ai_provider: IAIProvider):
        self.ai_provider = ai_provider
    
    def rank_papers(self, query: str, papers: List[Dict[str, Any]], 
                   ranking_mode: str = RankingMode.AI.value, limit: int = DEFAULT_LIMIT) -> List[Dict[str, Any]]:
        if ranking_mode == RankingMode.AI.value and self.ai_provider:
            return self.ai_provider.rank_papers(query, papers, limit)
        elif ranking_mode == RankingMode.CITATIONS.value:
            return self._rank_by_citations(papers, limit)
        elif ranking_mode == RankingMode.YEAR.value:
            return self._rank_by_year(papers, limit)
        else:
            return papers[:limit]
    
    def generate_summary(self, papers: List[Dict[str, Any]], query: str) -> str:
        if not self.ai_provider:
            return "AI provider not available for summary generation"
        
        try:
            return self.ai_provider.generate_summary(papers, query)
        except Exception as e:
            return f"Failed to generate summary: {str(e)}"
    
    def generate_research_insights(self, papers: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        if not self.ai_provider:
            return {"error": "AI provider not available"}
        
        try:
            return self.ai_provider.generate_insights(papers, query)
        except Exception as e:
            return {"error": f"Failed to generate insights: {str(e)}"}
    
    def _rank_by_citations(self, papers: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        def get_citations(paper):
            citations = paper.get('citations') or paper.get('citation') or 0
            try:
                return int(citations) if citations != self.CITATION_NA_VALUE else 0
            except (ValueError, TypeError):
                return 0
        
        sorted_papers = sorted(papers, key=get_citations, reverse=True)
        limited_papers = sorted_papers[:limit]
        self._add_ranking_explanations(limited_papers, RankingMode.CITATIONS.value)
        return limited_papers
    
    def _rank_by_year(self, papers: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        def get_year(paper):
            year = paper.get('year', 0)
            try:
                return int(year) if year != self.UNKNOWN_YEAR_VALUE else 0
            except (ValueError, TypeError):
                return 0
        
        sorted_papers = sorted(papers, key=get_year, reverse=True)
        limited_papers = sorted_papers[:limit]
        self._add_ranking_explanations(limited_papers, RankingMode.YEAR.value)
        return limited_papers
    
    def _add_ranking_explanations(self, papers: List[Dict[str, Any]], ranking_type: str) -> None:
        for i, paper in enumerate(papers):
            if ranking_type == RankingMode.CITATIONS.value:
                citations = paper.get('citations', self.CITATION_NA_VALUE)
                paper['explanation'] = f"Ranked #{i+1} by citations: {citations} citations"
            elif ranking_type == RankingMode.YEAR.value:
                year = paper.get('year', 'Unknown')
                paper['explanation'] = f"Ranked #{i+1} by year: {year} publication year"
