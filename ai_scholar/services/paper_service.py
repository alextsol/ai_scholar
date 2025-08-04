from typing import List, Optional, Dict, Any
from ..interfaces.ai_interface import IAIProvider
from ..interfaces.ranking_interface import IRankingProvider
from ..models.paper import Paper
from ..models.search_result import SearchResult
from ..config.settings import Settings
import time
import logging

logger = logging.getLogger(__name__)

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
        Aggregate papers from multiple sources and rank them using AI with intelligent pre-filtering
        
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
        
        # Statistics for transparency
        stats = {
            'total_collected': 0,
            'after_pre_filter': 0,
            'after_dedup': 0,
            'sent_to_ai': 0,
            'providers_used': {},
            'pre_ranking_applied': False
        }
        
        # Step 1: Collect from all providers with dynamic limits
        max_papers_for_ai = Settings.MAX_PAPERS_FOR_AI  # Maximum papers to send to AI model
        max_per_provider = min(limit, Settings.MAX_PER_PROVIDER)  # Cap individual provider results
        
        for backend_name, backend_func in self.search_providers.items():
            try:
                result = backend_func(query, max_per_provider, min_year, max_year)
                papers = self._extract_papers_from_result(result, backend_name)
                
                if papers:
                    stats['total_collected'] += len(papers)
                    # Pre-filter each provider's results for quality
                    quality_papers = self._pre_filter_papers(papers, query, backend_name)
                    stats['providers_used'][backend_name] = {
                        'raw_count': len(papers),
                        'after_filter': len(quality_papers)
                    }
                    aggregated_papers.extend(quality_papers)
                    sources_used.append(backend_name)
                    
            except Exception as e:
                continue
        
        if not aggregated_papers:
            return SearchResult(
                papers=[],
                query=query,
                total_found=0,
                processing_time=time.time() - start_time,
                ranking_mode=ranking_mode,
                backends_used=sources_used,
                aggregation_stats=stats
            )
        
        stats['after_pre_filter'] = len(aggregated_papers)
        
        # Step 2: Apply year filters
        if min_year is not None or max_year is not None:
            aggregated_papers = self._filter_papers_by_year(
                aggregated_papers, min_year, max_year
            )
        
        # Step 3: Remove duplicates
        unique_papers = self._remove_duplicates(aggregated_papers)
        stats['after_dedup'] = len(unique_papers)
        
        # Step 4: Intelligent pre-ranking to reduce AI workload
        if len(unique_papers) > max_papers_for_ai:
            # Pre-rank using fast heuristics before AI processing
            pre_ranked = self._fast_pre_rank(unique_papers, query, max_papers_for_ai)
            stats['pre_ranking_applied'] = True
            stats['sent_to_ai'] = len(pre_ranked)
        else:
            pre_ranked = unique_papers
            stats['sent_to_ai'] = len(pre_ranked)
        
        # Step 5: Final ranking
        ranked_papers = []
        ranking_applied = False
        
        if ranking_mode == 'ai' and self.ai_provider:
            try:
                ai_start_time = time.time()
                ranked_papers = self.ai_provider.rank_papers(
                    query, pre_ranked, ai_result_limit
                )
                ai_processing_time = time.time() - ai_start_time
                stats['ai_processing_time'] = ai_processing_time
                ranking_applied = True
                
                # Log performance metrics
                logger.info(f"Aggregate search optimization: {stats['total_collected']} → "
                          f"{stats['after_dedup']} → {stats['sent_to_ai']} → {len(ranked_papers)} papers. "
                          f"AI processing: {ai_processing_time:.2f}s")
                
            except Exception as e:
                logger.warning(f"AI ranking failed, falling back to citations: {str(e)}")
                # Fallback to citation-based ranking if AI fails
                ranked_papers = self._rank_by_citations(pre_ranked, ai_result_limit)
        elif ranking_mode == 'citations':
            ranked_papers = self._rank_by_citations(pre_ranked, ai_result_limit)
            ranking_applied = True
        elif ranking_mode == 'year':
            ranked_papers = self._rank_by_year(pre_ranked, ai_result_limit)
            ranking_applied = True
        else:
            ranked_papers = pre_ranked[:ai_result_limit]
        
        # Clean up temporary scoring fields
        self._cleanup_temporary_fields(ranked_papers)
        
        final_papers = self._merge_ranked_with_details(ranked_papers, aggregated_papers)        # Convert dict papers to Paper objects
        paper_objects = []
        for paper_dict in final_papers[:ai_result_limit]:
            # Create Paper object from dictionary
            paper_obj = Paper(
                title=paper_dict.get('title', ''),
                authors=paper_dict.get('authors', ''),
                abstract=paper_dict.get('abstract', ''),
                year=paper_dict.get('year'),
                url=paper_dict.get('url', ''),
                citations=paper_dict.get('citations', 0),
                source=paper_dict.get('source', ''),
                published=paper_dict.get('published', ''),
                explanation=paper_dict.get('explanation', '')
            )
            paper_objects.append(paper_obj)
        
        return SearchResult(
            papers=paper_objects,
            query=query,
            total_found=len(final_papers),
            processing_time=time.time() - start_time,
            ranking_mode=ranking_mode,
            backends_used=sources_used,
            aggregation_stats=stats
        )
    
    def get_paper_details(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific paper"""
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
                from ...utils.utils import format_items
                papers = format_items(result.get("results", []), result.get("mapping", {}))
            else:
                from ...utils.utils import generic_requests_search
                papers = generic_requests_search(
                    result.get("url"), 
                    result.get("params"), 
                    mapping=result.get("mapping"), 
                    extractor=result.get("extractor")
                )
        elif isinstance(result, list):
            papers = result
        
        if not isinstance(papers, list) or not all(isinstance(paper, dict) for paper in papers):
            return []
        
        for paper in papers:
            paper['source'] = backend_name
        
        return papers
    
    def _filter_papers_by_year(self, papers: List[Dict[str, Any]], 
                              min_year: Optional[int], max_year: Optional[int]) -> List[Dict[str, Any]]:
        """Filter papers by publication year"""
        if min_year is None and max_year is None:
            return papers
        
        filtered_papers = []
        for paper in papers:
            try:
                year_val = paper.get('year', 0)
                year = int(year_val) if year_val is not None else 0
                if (min_year is None or year >= min_year) and (max_year is None or year <= max_year):
                    filtered_papers.append(paper)
            except (ValueError, TypeError):
                continue
        return filtered_papers
    
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
    
    def _pre_filter_papers(self, papers: List[Dict[str, Any]], query: str, provider: str) -> List[Dict[str, Any]]:
        """Pre-filter papers from each provider to improve quality before aggregation"""
        if not papers:
            return papers
        
        filtered = []
        query_words = set(query.lower().split())
        
        for paper in papers:
            # Basic quality checks
            title = paper.get('title', '').strip()
            authors = paper.get('authors', '').strip()
            abstract = paper.get('abstract', '').strip()
            
            # Skip papers without essential information
            if not title or len(title) < 10:
                continue
            if not authors or authors.lower() in ['unknown', 'n/a', 'no authors']:
                continue
            
            # Calculate relevance score for this paper
            relevance_score = self._calculate_relevance_score(paper, query_words)
            
            # Quality score based on available metadata
            quality_score = self._calculate_quality_score(paper)
            
            # Combined score
            combined_score = (relevance_score * 0.7) + (quality_score * 0.3)
            paper['_pre_filter_score'] = combined_score
            
            # Only keep papers above a minimum threshold
            if combined_score > Settings.PRE_FILTER_MIN_SCORE:  # Configurable threshold
                filtered.append(paper)
        
        # Sort by score and return top papers from this provider
        filtered.sort(key=lambda x: x.get('_pre_filter_score', 0), reverse=True)
        max_per_provider = Settings.MAX_PER_PROVIDER_AFTER_FILTER  # Limit per provider to prevent one source dominating
        return filtered[:max_per_provider]
    
    def _calculate_relevance_score(self, paper: Dict[str, Any], query_words: set) -> float:
        """Calculate relevance score based on query matching"""
        score = 0.0
        title = paper.get('title', '').lower()
        abstract = paper.get('abstract', '').lower()
        
        # Title matching (higher weight)
        title_words = set(title.split())
        title_matches = len(query_words.intersection(title_words))
        if title_matches > 0:
            score += (title_matches / len(query_words)) * 0.6
        
        # Abstract matching (lower weight)
        if abstract:
            abstract_words = set(abstract.split())
            abstract_matches = len(query_words.intersection(abstract_words))
            if abstract_matches > 0:
                score += (abstract_matches / len(query_words)) * 0.4
        
        # Exact phrase matching (bonus)
        query_text = ' '.join(query_words)
        if query_text in title:
            score += 0.3
        elif query_text in abstract:
            score += 0.2
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _calculate_quality_score(self, paper: Dict[str, Any]) -> float:
        """Calculate quality score based on available metadata"""
        score = 0.0
        
        # Has DOI (indicator of published work)
        if paper.get('doi'):
            score += 0.3
        
        # Has URL (accessible)
        if paper.get('url'):
            score += 0.2
        
        # Has abstract (more informative)
        abstract = paper.get('abstract', '')
        if abstract and len(abstract) > 100:
            score += 0.3
        elif abstract and len(abstract) > 50:
            score += 0.2
        
        # Has citation count (indicates impact)
        citations = paper.get('citations')
        if citations and citations != 'N/A':
            try:
                cite_count = int(citations)
                if cite_count > 100:
                    score += 0.2
                elif cite_count > 10:
                    score += 0.1
            except:
                pass
        
        # Recent publication (within last 10 years)
        year = paper.get('year')
        if year and year != 'Unknown':
            try:
                pub_year = int(year)
                current_year = 2024
                if current_year - pub_year <= 10:
                    score += 0.1
            except:
                pass
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _fast_pre_rank(self, papers: List[Dict[str, Any]], query: str, target_count: int) -> List[Dict[str, Any]]:
        """Fast pre-ranking to reduce papers before AI processing"""
        if len(papers) <= target_count:
            return papers
        
        query_words = set(query.lower().split())
        
        # Score each paper using fast heuristics
        for paper in papers:
            score = 0.0
            
            # Relevance component (50%)
            relevance = self._calculate_relevance_score(paper, query_words)
            score += relevance * 0.5
            
            # Quality component (30%)
            quality = self._calculate_quality_score(paper)
            score += quality * 0.3
            
            # Citation impact (20%)
            citations = paper.get('citations', 0)
            if citations and citations != 'N/A':
                try:
                    cite_count = int(citations)
                    # Normalize citation count (log scale to prevent dominance by highly cited papers)
                    import math
                    citation_score = min(math.log10(cite_count + 1) / 3.0, 1.0)
                    score += citation_score * 0.2
                except:
                    pass
            
            paper['_fast_rank_score'] = score
        
        # Sort by score and return top candidates
        papers.sort(key=lambda x: x.get('_fast_rank_score', 0), reverse=True)
        return papers[:target_count]
    
    def _cleanup_temporary_fields(self, papers: List[Dict[str, Any]]) -> None:
        """Remove temporary scoring fields from papers"""
        temp_fields = ['_pre_filter_score', '_fast_rank_score', '_quality_score']
        for paper in papers:
            for field in temp_fields:
                paper.pop(field, None)
    
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
                    merged_paper = full_paper.copy()
                    if 'explanation' in ranked_paper:
                        merged_paper['explanation'] = ranked_paper['explanation']
                    merged.append(merged_paper)
                    break
            else:
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
        relevance_data = []
        for i, paper in enumerate(papers):
            relevance_score = len(paper.get('title', '')) / 100.0
            relevance_data.append({'index': i, 'relevance': relevance_score})
        
        relevance_data.sort(key=lambda x: x['relevance'], reverse=True)
        return {
            'ranking': relevance_data,
            'most_relevant': relevance_data[0] if relevance_data else None,
            'average': sum(x['relevance'] for x in relevance_data) / len(relevance_data) if relevance_data else 0
        }
