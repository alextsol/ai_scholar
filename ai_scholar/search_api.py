from typing import List, Dict, Any, Optional
from .paper_aggregator import aggregate_and_rank_papers
from .config import SearchConfig

class AIScholar:

    @staticmethod
    def search_papers(
        query: str,
        limit: int = SearchConfig.DEFAULT_LIMIT,
        ai_result_limit: int = SearchConfig.DEFAULT_AI_RESULT_LIMIT,
        ranking_mode: str = "ai_ranking",
        min_year: Optional[int] = None,
        max_year: Optional[int] = None
    ) -> List[Dict[str, Any]]:

        return aggregate_and_rank_papers(
            query=query,
            limit=limit,
            ai_result_limit=min(ai_result_limit, SearchConfig.MAX_AI_RESULT_LIMIT),
            ranking_mode=ranking_mode,
            min_year=min_year,
            max_year=max_year
        )
    
    @staticmethod
    def search_simple(query: str, count: int = 10) -> List[Dict[str, Any]]:
        return AIScholar.search_papers(
            query=query,
            limit=count * 2,
            ai_result_limit=count,
            ranking_mode="ai_ranking"
        )[:count]
