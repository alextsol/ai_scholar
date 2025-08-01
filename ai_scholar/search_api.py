from typing import List, Dict, Any, Optional
from .services.service_factory import ServiceFactory
from .config import SearchConfig

class AIScholar:
    def __init__(self):
        self.service_factory = ServiceFactory()
        self.service_factory.initialize_services()
    
    def search_papers(
        self,
        query: str,
        limit: int = SearchConfig.DEFAULT_LIMIT,
        ai_result_limit: int = SearchConfig.DEFAULT_AI_RESULT_LIMIT,
        ranking_mode: str = "ai_ranking",
        min_year: Optional[int] = None,
        max_year: Optional[int] = None
    ) -> List[Dict[str, Any]]:

        paper_service = self.service_factory.get_paper_service()
        result = paper_service.aggregate_and_rank_papers(
            query=query,
            limit=limit,
            ai_result_limit=min(ai_result_limit, SearchConfig.MAX_AI_RESULT_LIMIT),
            ranking_mode=ranking_mode,
            min_year=min_year,
            max_year=max_year
        )
        return result.to_dict()
    
    def search_simple(self, query: str, count: int = 10) -> List[Dict[str, Any]]:
        return self.search_papers(
            query=query,
            limit=count * 2,
            ai_result_limit=count,
            ranking_mode="ai_ranking"
        )[:count]
