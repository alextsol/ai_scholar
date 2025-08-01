from typing import List, Optional, Dict, Any
from ..interfaces.ai_interface import IAIProvider
from ..interfaces.ranking_interface import IRankingProvider
from ..models.paper import Paper
from ..models.search_result import SearchResult
import time

class PaperService:
    """Service for handling paper aggregation, ranking, and analysis"""
    
    def __init__(self, search_providers: Dict[str, Any], ai_provider: IAIProvider, 
                 ranking_provider: IRankingProvider):
        self.search_providers = search_providers
        self.ai_provider = ai_provider
        self.ranking_provider = ranking_provider
    
    def aggregate_and_rank_papers(self, query: str, limit: int, ai_result_limit: int,
                                ranking_mode: str, min_year: Optional[int] = None,
                                max_year: Optional[int] = None) -> SearchResult:
        """
        Aggregate papers from multiple sources and rank them using AI
        
        Args:
            query: Search query
            limit: Limit per source
            ai_result_limit: Final number of results after ranking
            ranking_mode: Mode for ranking ('ai', 'citations', 'year')
            min_year: Minimum publication year
            max_year: Maximum publication year
            
        Returns:
            SearchResult with aggregated and ranked papers
        """
        start_time = time.time()
        aggregated_papers = []
        sources_used = []
        
        # Aggregate from all available sources
        for backend_name, backend_func in self.search_providers.items():
            try:
                result = backend_func(query, limit)
                papers = self._extract_papers_from_result(result, backend_name)
                
                if papers:
                    aggregated_papers.extend(papers)
                    sources_used.append(backend_name)
                    
            except Exception as e:
                print(f"Error with backend {backend_name}: {e}")
                continue
        
        if not aggregated_papers:
            return SearchResult(
                papers=[],
                total_count=0,
                backend_used='aggregate',
                sources_used=sources_used,
                search_time=time.time() - start_time,
                ranking_applied=False
            )
        
        # Filter by year if specified
        if min_year is not None or max_year is not None:
            aggregated_papers = self._filter_papers_by_year(
                aggregated_papers, min_year, max_year
            )
        
        # Remove duplicates
        unique_papers = self._remove_duplicates(aggregated_papers)
        
        # Rank papers
        ranked_papers = []
        ranking_applied = False
        
        if ranking_mode == 'ai' and self.ai_provider:
            try:
                ranked_papers = self.ai_provider.rank_papers(
                    query, unique_papers, ai_result_limit
                )
                ranking_applied = True
            except Exception as e:
                print(f"AI ranking failed: {e}")
                ranked_papers = unique_papers[:ai_result_limit]
        elif ranking_mode == 'citations':
            ranked_papers = self._rank_by_citations(unique_papers, ai_result_limit)
            ranking_applied = True
        elif ranking_mode == 'year':
            ranked_papers = self._rank_by_year(unique_papers, ai_result_limit)
            ranking_applied = True
        else:
            ranked_papers = unique_papers[:ai_result_limit]
        
        # Merge ranked results with full paper details
        final_papers = self._merge_ranked_with_details(ranked_papers, aggregated_papers)
        
        return SearchResult(
            papers=final_papers[:ai_result_limit],
            total_count=len(final_papers),
            backend_used='aggregate',
            sources_used=sources_used,
            search_time=time.time() - start_time,
            ranking_applied=ranking_applied
        )
    
    def get_paper_details(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific paper"""
        # This would typically query a database or external API
        # For now, return None as placeholder
        return None
    
    def compare_papers(self, papers: List[Dict[str, Any]], 
                      criteria: List[str]) -> Dict[str, Any]:
        """Compare multiple papers based on specified criteria"""
        comparison_result = {
            'papers': papers,
            'criteria': criteria,
            'comparison_matrix': {},
            'summary': {}
        }
        
        for criterion in criteria:
            if criterion == 'citations':
                comparison_result['comparison_matrix'][criterion] = self._compare_by_citations(papers)
            elif criterion == 'year':
                comparison_result['comparison_matrix'][criterion] = self._compare_by_year(papers)
            elif criterion == 'relevance':
                comparison_result['comparison_matrix'][criterion] = self._compare_by_relevance(papers)
        
        return comparison_result
    
    def _extract_papers_from_result(self, result: Any, backend_name: str) -> List[Dict[str, Any]]:
        """Extract papers from search result based on backend format"""
        papers = None
        
        if isinstance(result, dict):
            if backend_name == "arxiv":
                # Handle arXiv specific format
                from utils.utils import format_items
                papers = format_items(result.get("results", []), result.get("mapping", {}))
            else:
                # Handle generic format
                from utils.utils import generic_requests_search
                papers = generic_requests_search(
                    result.get("url"), 
                    result.get("params"), 
                    mapping=result.get("mapping"), 
                    extractor=result.get("extractor")
                )
        elif isinstance(result, list):
            papers = result
        
        # Validate papers format
        if not isinstance(papers, list) or not all(isinstance(paper, dict) for paper in papers):
            return []
        
        # Add source information
        for paper in papers:
            paper['source'] = backend_name
        
        return papers
    
    def _filter_papers_by_year(self, papers: List[Dict[str, Any]], 
                              min_year: Optional[int], max_year: Optional[int]) -> List[Dict[str, Any]]:
        """Filter papers by publication year"""
        from utils.utils import filter_results_by_year
        return filter_results_by_year(papers, min_year, max_year)
    
    def _remove_duplicates(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate papers based on title similarity"""
        seen = set()
        unique = []
        
        for paper in papers:
            title = paper.get('title', '').lower().strip()
            if title and title not in seen:
                seen.add(title)
                unique.append(paper)
        
        return unique
    
    def _rank_by_citations(self, papers: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        """Rank papers by citation count"""
        def get_citations(paper):
            citations = paper.get('citations') or paper.get('citation') or 0
            try:
                return int(citations) if citations != 'N/A' else 0
            except (ValueError, TypeError):
                return 0
        
        sorted_papers = sorted(papers, key=get_citations, reverse=True)
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
        return sorted_papers[:limit]
    
    def _merge_ranked_with_details(self, ranked_papers: List[Dict[str, Any]], 
                                  all_papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge ranked results with full paper details"""
        merged = []
        
        for ranked_paper in ranked_papers:
            # Find corresponding paper in all_papers with full details
            title = ranked_paper.get('title', '').lower().strip()
            
            for full_paper in all_papers:
                if full_paper.get('title', '').lower().strip() == title:
                    # Merge ranking information
                    merged_paper = full_paper.copy()
                    if 'explanation' in ranked_paper:
                        merged_paper['explanation'] = ranked_paper['explanation']
                    merged.append(merged_paper)
                    break
            else:
                # If not found, use the ranked paper as is
                merged.append(ranked_paper)
        
        return merged
    
    def _compare_by_citations(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare papers by citation count"""
        citation_data = []
        for i, paper in enumerate(papers):
            citations = paper.get('citations') or paper.get('citation') or 0
            try:
                citation_count = int(citations) if citations != 'N/A' else 0
            except (ValueError, TypeError):
                citation_count = 0
            citation_data.append({'index': i, 'citations': citation_count})
        
        citation_data.sort(key=lambda x: x['citations'], reverse=True)
        return {
            'ranking': citation_data,
            'highest': citation_data[0] if citation_data else None,
            'average': sum(x['citations'] for x in citation_data) / len(citation_data) if citation_data else 0
        }
    
    def _compare_by_year(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare papers by publication year"""
        year_data = []
        for i, paper in enumerate(papers):
            year = paper.get('year', 0)
            try:
                year_val = int(year) if year != 'Unknown year' else 0
            except (ValueError, TypeError):
                year_val = 0
            year_data.append({'index': i, 'year': year_val})
        
        year_data.sort(key=lambda x: x['year'], reverse=True)
        return {
            'ranking': year_data,
            'newest': year_data[0] if year_data else None,
            'oldest': year_data[-1] if year_data else None,
            'average': sum(x['year'] for x in year_data) / len(year_data) if year_data else 0
        }
    
    def _compare_by_relevance(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare papers by relevance (placeholder implementation)"""
        # This would need actual relevance scoring logic
        relevance_data = []
        for i, paper in enumerate(papers):
            # Simple placeholder scoring based on title length as relevance
            relevance_score = len(paper.get('title', '')) / 100.0
            relevance_data.append({'index': i, 'relevance': relevance_score})
        
        relevance_data.sort(key=lambda x: x['relevance'], reverse=True)
        return {
            'ranking': relevance_data,
            'most_relevant': relevance_data[0] if relevance_data else None,
            'average': sum(x['relevance'] for x in relevance_data) / len(relevance_data) if relevance_data else 0
        }
