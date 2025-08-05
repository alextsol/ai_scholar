from typing import List, Optional, Dict, Any
from ..interfaces.ai_interface import IAIProvider
from ..interfaces.ranking_interface import IRankingProvider
from ..models.paper import Paper
from ..models.search_result import SearchResult
from ..config.settings import Settings
from ..enums import ProviderType, RankingMode
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
        
        providers_to_use, per_provider_limits = self._optimize_provider_usage(
            ranking_mode, limit, ai_result_limit
        )
        
        max_papers_for_ai = Settings.MAX_PAPERS_FOR_AI
        
        for backend_name, backend_func in self.search_providers.items():
            # Skip providers that don't support the ranking mode requirements
            if backend_name not in providers_to_use:
                logger.info(f"Skipping {backend_name} (not in providers_to_use)")
                continue
                
            try:
                provider_limit = per_provider_limits.get(backend_name, limit)
                logger.info(f"Calling {backend_name} with limit {provider_limit}")
                result = backend_func(query, provider_limit, min_year, max_year)
                papers = self._extract_papers_from_result(result, backend_name)
                logger.info(f"{backend_name} returned {len(papers) if papers else 0} papers")
                
                if papers:
                    stats['total_collected'] += len(papers)
                    # Pre-filter each provider's results for quality
                    try:
                        quality_papers = self._pre_filter_papers(papers, query, backend_name)
                        logger.info(f"{backend_name} after filtering: {len(quality_papers)} papers")
                        stats['providers_used'][backend_name] = {
                            'raw_count': len(papers),
                            'after_filter': len(quality_papers)
                        }
                        aggregated_papers.extend(quality_papers)
                        sources_used.append(backend_name)
                    except Exception as filter_error:
                        logger.error(f"Error filtering {backend_name} papers: {str(filter_error)}")
                        # If filtering fails, use papers without filtering but with source info
                        for paper in papers:
                            paper['source'] = backend_name
                        stats['providers_used'][backend_name] = {
                            'raw_count': len(papers),
                            'after_filter': len(papers)
                        }
                        aggregated_papers.extend(papers)
                        sources_used.append(backend_name)
                        logger.info(f"{backend_name} used without filtering: {len(papers)} papers")
                else:
                    logger.info(f"{backend_name} returned no papers")
                    stats['providers_used'][backend_name] = {
                        'raw_count': 0,
                        'after_filter': 0
                    }
                    
            except Exception as e:
                logger.error(f"Error calling {backend_name}: {str(e)}")
                stats['providers_used'][backend_name] = {
                    'raw_count': 0,
                    'after_filter': 0
                }
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
        
        if min_year is not None or max_year is not None:
            aggregated_papers = self._filter_papers_by_year(
                aggregated_papers, min_year, max_year
            )
        
        unique_papers = self._remove_duplicates(aggregated_papers)
        stats['after_dedup'] = len(unique_papers)
        
        if len(unique_papers) > max_papers_for_ai:
            pre_ranked = self._fast_pre_rank(unique_papers, query, max_papers_for_ai)
            stats['pre_ranking_applied'] = True
            stats['sent_to_ai'] = len(pre_ranked)
        else:
            pre_ranked = unique_papers
            stats['sent_to_ai'] = len(pre_ranked)
        
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
            ranked_papers = self._rank_by_citations_with_diversity(pre_ranked, ai_result_limit)
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
    
    def _optimize_provider_usage(self, ranking_mode: str, limit: int, ai_result_limit: int) -> tuple:
        """
        Optimize provider selection and limits based on ranking mode requirements
        
        Args:
            ranking_mode: The ranking mode being used
            limit: Base limit per provider
            ai_result_limit: Final number of results needed
            
        Returns:
            Tuple of (providers_to_use, per_provider_limits)
        """
        # Define which providers support citations
        citation_providers = [ProviderType.SEMANTIC_SCHOLAR.value, ProviderType.CROSSREF.value, 
                             ProviderType.OPENALEX.value, ProviderType.CORE.value, 
                             ProviderType.OPENCITATIONS.value]
        all_providers = list(self.search_providers.keys())
        
        if ranking_mode == RankingMode.CITATIONS.value:
            # For citation-based ranking, focus on providers with citation data
            providers_to_use = [p for p in all_providers if p in citation_providers]
            
            target_total = max(ai_result_limit * 10, 500)
            per_provider_base = min(target_total // len(providers_to_use), Settings.MAX_PER_PROVIDER)
            
            for provider in providers_to_use:
                if provider == ProviderType.SEMANTIC_SCHOLAR.value:
                    per_provider_limits[provider] = min(per_provider_base * 2, Settings.MAX_PER_PROVIDER)
                elif provider == ProviderType.CROSSREF.value:
                    # CrossRef is reliable for citation counts
                    per_provider_limits[provider] = min(per_provider_base * 1.5, Settings.MAX_PER_PROVIDER)
                elif provider == ProviderType.OPENALEX.value:
                    # OpenAlex has good coverage
                    per_provider_limits[provider] = min(per_provider_base * 1.5, Settings.MAX_PER_PROVIDER)
                elif provider == ProviderType.OPENCITATIONS.value:
                    # OpenCitations excels in citation analysis and bibliometric data
                    per_provider_limits[provider] = min(per_provider_base * 1.3, Settings.MAX_PER_PROVIDER)
                else:
                    # Core and others get standard limit
                    per_provider_limits[provider] = per_provider_base
                    
            logger.info(f"Citation mode: Using {len(providers_to_use)} providers with enhanced limits for citation data")
            logger.info(f"Provider limits: {per_provider_limits}")
            
        elif ranking_mode == RankingMode.YEAR.value:
            # For newest papers ranking, use all providers but optimize for recency and coverage
            providers_to_use = all_providers
            
            target_total = max(ai_result_limit * 8, 400)
            per_provider_base = min(target_total // len(providers_to_use), Settings.MAX_PER_PROVIDER)
            
            per_provider_limits = {}
            for provider in providers_to_use:
                if provider == ProviderType.ARXIV.value:
                    per_provider_limits[provider] = min(per_provider_base * 2, Settings.MAX_PER_PROVIDER)
                elif provider == ProviderType.SEMANTIC_SCHOLAR.value:
                    per_provider_limits[provider] = min(per_provider_base * 1.8, Settings.MAX_PER_PROVIDER)
                elif provider == ProviderType.OPENALEX.value:
                    per_provider_limits[provider] = min(per_provider_base * 1.5, Settings.MAX_PER_PROVIDER)
                elif provider == ProviderType.CROSSREF.value:
                    # CrossRef for published recent work
                    per_provider_limits[provider] = min(per_provider_base * 1.3, Settings.MAX_PER_PROVIDER)
                else:
                    per_provider_limits[provider] = per_provider_base
                    
            logger.info(f"Year mode: Using {len(providers_to_use)} providers optimized for recent papers")
            logger.info(f"Provider limits: {per_provider_limits}")
            
        else:
            providers_to_use = all_providers
            max_per_provider = min(limit, Settings.MAX_PER_PROVIDER)
            per_provider_limits = {provider: max_per_provider for provider in providers_to_use}
            logger.info(f"Standard mode: Using {len(providers_to_use)} providers with uniform limits")
        
        return providers_to_use, per_provider_limits
    
    
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
            if backend_name == ProviderType.ARXIV.value:
                from ..utils.helpers import format_items
                papers = format_items(result.get("results", []), result.get("mapping", {}))
            else:
                from ..utils.helpers import generic_requests_search
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
            try:
                # Basic quality checks with safe string handling
                title = paper.get('title', '')
                if isinstance(title, list):
                    title = ' '.join(str(t) for t in title if t is not None)
                elif title is None:
                    title = ''
                title = str(title).strip()
                
                authors = paper.get('authors', '')
                if isinstance(authors, list):
                    authors = ', '.join(str(a) for a in authors if a is not None)
                elif authors is None:
                    authors = ''
                authors = str(authors).strip()
                
                abstract = paper.get('abstract', '')
                if isinstance(abstract, list):
                    abstract = ' '.join(str(a) for a in abstract if a is not None)
                elif abstract is None:
                    abstract = ''
                abstract = str(abstract).strip()
                
                # Skip papers without essential information
                if not title or len(title) < 10:
                    continue
                if not authors or authors.lower() in ['unknown', 'n/a', 'no authors']:
                    continue
                
                # Update paper with cleaned fields
                paper['title'] = title
                paper['authors'] = authors
                paper['abstract'] = abstract
                
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
                    
            except Exception as e:
                continue
        
        filtered.sort(key=lambda x: x.get('_pre_filter_score', 0), reverse=True)
        max_per_provider = Settings.MAX_PER_PROVIDER_AFTER_FILTER
        return filtered[:max_per_provider]
    
    def _calculate_relevance_score(self, paper: Dict[str, Any], query_words: set) -> float:
        """Calculate relevance score based on query matching"""
        score = 0.0
        
        # Safe string handling for title
        title = paper.get('title', '')
        if isinstance(title, list):
            title = ' '.join(str(t) for t in title)
        title = str(title).lower() if title else ''
        
        # Safe string handling for abstract
        abstract = paper.get('abstract', '')
        if isinstance(abstract, list):
            abstract = ' '.join(str(a) for a in abstract)
        abstract = str(abstract).lower() if abstract else ''
        
        # Title matching (higher weight)
        if title:
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
        
        # Has abstract (more informative) - safe string handling
        abstract = paper.get('abstract', '')
        if isinstance(abstract, list):
            abstract = ' '.join(str(a) for a in abstract)
        abstract = str(abstract) if abstract else ''
        
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
        temp_fields = ['_pre_filter_score', '_fast_rank_score', '_quality_score', 
                      '_year_relevance_score', '_year_score_components']
        for paper in papers:
            for field in temp_fields:
                paper.pop(field, None)
    
    def _rank_by_citations(self, papers: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        """Rank papers by citation count and add custom explanations for each paper"""
        def get_citations(paper):
            citations = paper.get('citations') or paper.get('citation') or 0
            try:
                return int(citations) if citations != 'N/A' else 0
            except (ValueError, TypeError):
                return 0
        
        # Filter out papers without citation data to improve quality
        papers_with_citations = []
        papers_without_citations = []
        
        for paper in papers:
            citations = get_citations(paper)
            if citations > 0:
                papers_with_citations.append(paper)
            else:
                papers_without_citations.append(paper)
        
        # Sort papers with citations by citation count
        sorted_cited_papers = sorted(papers_with_citations, key=get_citations, reverse=True)
        
        # If we need more papers, include some without citations (sorted by year/quality)
        if len(sorted_cited_papers) < limit and papers_without_citations:
            remaining_needed = limit - len(sorted_cited_papers)
            # Sort papers without citations by year (newest first) as fallback
            sorted_uncited = sorted(papers_without_citations, 
                                  key=lambda p: p.get('year', 0) if str(p.get('year', 0)).isdigit() else 0, 
                                  reverse=True)
            sorted_papers = sorted_cited_papers + sorted_uncited[:remaining_needed]
        else:
            sorted_papers = sorted_cited_papers
        
        # Add custom explanations tailored to each paper's content
        for i, paper in enumerate(sorted_papers[:limit]):
            citations = get_citations(paper)
            rank = i + 1
            title = paper.get('title', '')
            authors = paper.get('authors', '')
            year = paper.get('year', '')
            abstract = paper.get('abstract', '')
            
            # Generate custom explanation based on paper's actual content
            explanation = self._generate_citation_explanation(
                paper=paper,
                rank=rank,
                citations=citations,
                title=title,
                authors=authors,
                year=year,
                abstract=abstract
            )
            
            paper['explanation'] = explanation
        
        return sorted_papers[:limit]
    
    def _rank_by_year(self, papers: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        """
        Rank papers by publication year with relevance weighting for optimal recent & relevant results
        Combines recency with relevance to find the most valuable up-to-date papers
        """
        def get_year(paper):
            year = paper.get('year', 0)
            try:
                return int(year) if year != 'Unknown year' else 0
            except (ValueError, TypeError):
                return 0
        
        current_year = 2025
        
        # Enhanced ranking: combine recency with relevance and quality
        def calculate_year_relevance_score(paper):
            # Recency score (0.0 to 1.0, with recent papers getting higher scores)
            year = get_year(paper)
            if year <= 0:
                recency_score = 0.0
            else:
                age = current_year - year
                if age <= 1:
                    recency_score = 1.0  # Very recent (2024-2025)
                elif age <= 2:
                    recency_score = 0.9  # Recent (2023)
                elif age <= 3:
                    recency_score = 0.8  # Contemporary (2022)
                elif age <= 5:
                    recency_score = 0.7  # Modern (2020-2021)
                elif age <= 10:
                    recency_score = 0.5  # Established (2015-2019)
                else:
                    recency_score = 0.2  # Historical (pre-2015)
            
            # Quality/relevance score from pre-filtering
            quality_score = paper.get('_pre_filter_score', 0.5)
            
            # Citation bonus for recent high-impact work
            citation_bonus = 0.0
            citations = paper.get('citations', 0)
            if citations and citations != 'N/A':
                try:
                    cite_count = int(citations)
                    if year >= 2020:  # Only boost recent papers with citations
                        if cite_count > 100:
                            citation_bonus = 0.2
                        elif cite_count > 50:
                            citation_bonus = 0.15
                        elif cite_count > 20:
                            citation_bonus = 0.1
                        elif cite_count > 5:
                            citation_bonus = 0.05
                except:
                    pass
            
            # Venue quality indicator (if available)
            venue_bonus = 0.0
            venue = paper.get('venue', '').lower()
            if any(term in venue for term in ['nature', 'science', 'cell', 'nejm', 'lancet']):
                venue_bonus = 0.15
            elif any(term in venue for term in ['ieee', 'acm', 'springer', 'elsevier']):
                venue_bonus = 0.1
            
            # Combine scores: recency (50%) + quality (30%) + citations (15%) + venue (5%)
            final_score = (recency_score * 0.5) + (quality_score * 0.3) + (citation_bonus * 0.15) + (venue_bonus * 0.05)
            
            # Store components for explanation generation
            paper['_year_score_components'] = {
                'recency': recency_score,
                'quality': quality_score,
                'citation_bonus': citation_bonus,
                'venue_bonus': venue_bonus,
                'final': final_score,
                'year': year
            }
            
            return final_score
        
        # Calculate scores and sort by combined relevance-recency score
        for paper in papers:
            paper['_year_relevance_score'] = calculate_year_relevance_score(paper)
        
        # Sort by combined score (primary) and then by year (secondary)
        sorted_papers = sorted(papers, 
                             key=lambda p: (p.get('_year_relevance_score', 0), get_year(p)), 
                             reverse=True)
        
        # Add custom explanations tailored to each paper's content and ranking factors
        for i, paper in enumerate(sorted_papers[:limit]):
            year = get_year(paper)
            rank = i + 1
            title = paper.get('title', '')
            authors = paper.get('authors', '')
            abstract = paper.get('abstract', '')
            score_components = paper.get('_year_score_components', {})
            
            # Generate custom explanation based on paper's actual content and ranking factors
            explanation = self._generate_enhanced_year_explanation(
                paper=paper,
                rank=rank,
                year=year,
                title=title,
                authors=authors,
                abstract=abstract,
                score_components=score_components
            )
            
            paper['explanation'] = explanation
        
        return sorted_papers[:limit]
    
    def _rank_by_citations_with_diversity(self, papers: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        """Enhanced citation ranking that ensures OpenCitations representation when present"""
        
        opencitations_papers = [p for p in papers if p.get('source') == 'opencitations']
        other_papers = [p for p in papers if p.get('source') != 'opencitations']
        
        if opencitations_papers and len(other_papers) > 0:
            all_ranked = self._rank_by_citations(papers, limit * 2)
            
            min_opencitations = max(2, min(len(opencitations_papers), max(limit // 3, limit // 5)))
            
            top_opencitations = [p for p in all_ranked if p.get('source') == 'opencitations'][:min_opencitations]
            
            opencitations_titles = {p.get('title', '') for p in top_opencitations}
            top_others = [p for p in all_ranked 
                         if p.get('source') != 'opencitations' or p.get('title', '') not in opencitations_titles]
            
            final_papers = []
            oc_used = 0
            other_used = 0
            
            for paper in all_ranked:
                if len(final_papers) >= limit:
                    break
                    
                is_opencitations = paper.get('source') == 'opencitations'
                
                if is_opencitations and oc_used < min_opencitations:
                    final_papers.append(paper)
                    oc_used += 1
                elif not is_opencitations and other_used < (limit - min_opencitations):
                    final_papers.append(paper)
                    other_used += 1
            
            remaining_slots = limit - len(final_papers)
            if remaining_slots > 0:
                used_titles = {p.get('title', '') for p in final_papers}
                for paper in all_ranked:
                    if len(final_papers) >= limit:
                        break
                    if paper.get('title', '') not in used_titles:
                        final_papers.append(paper)
            
            logger.info(f"Citation ranking with diversity: {len(final_papers)} total "
                       f"({oc_used} OpenCitations, {len(final_papers) - oc_used} others)")
            
            return final_papers[:limit]
        else:
            return self._rank_by_citations(papers, limit)
    
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
        """Compare papers by relevance"""
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
    
    def _generate_citation_explanation(self, paper: Dict[str, Any], rank: int, citations: int,
                                     title: str, authors: str, year: str, abstract: str) -> str:
        """Generate custom explanation for citation-based ranking"""
        
        # Extract key content indicators from the paper
        content_indicators = []
        
        # Analyze title for key terms
        title_lower = title.lower()
        if any(term in title_lower for term in ['survey', 'review', 'comprehensive']):
            content_indicators.append('comprehensive survey work')
        elif any(term in title_lower for term in ['novel', 'new', 'innovative']):
            content_indicators.append('innovative research')
        elif any(term in title_lower for term in ['deep', 'neural', 'machine learning', 'ai']):
            content_indicators.append('cutting-edge AI research')
        elif any(term in title_lower for term in ['analysis', 'study', 'investigation']):
            content_indicators.append('analytical study')
        
        # Analyze authors for recognizable patterns
        author_insight = ""
        if authors and ',' in authors:
            author_count = len(authors.split(','))
            if author_count > 5:
                author_insight = f"collaborative work with {author_count} researchers"
            elif author_count > 2:
                author_insight = f"multi-author collaboration"
        
        # Analyze abstract for methodology clues
        method_insights = []
        if abstract:
            abstract_lower = abstract.lower()
            if any(term in abstract_lower for term in ['experiment', 'empirical', 'evaluation']):
                method_insights.append('empirical evaluation')
            if any(term in abstract_lower for term in ['dataset', 'data', 'benchmark']):
                method_insights.append('data-driven analysis')
            if any(term in abstract_lower for term in ['algorithm', 'method', 'approach']):
                method_insights.append('methodological contribution')
            if any(term in abstract_lower for term in ['performance', 'accuracy', 'results']):
                method_insights.append('performance validation')
        
        # Create custom explanation
        explanation_parts = []
        
        # Start with ranking and citation count
        if citations > 0:
            explanation_parts.append(f"Ranked #{rank} with {citations:,} citations")
        else:
            explanation_parts.append(f"Ranked #{rank} (limited citation data available)")
        
        # Add content-specific reasoning
        if content_indicators:
            explanation_parts.append(f"as {content_indicators[0]}")
        
        # Add methodological insight
        if method_insights:
            if len(method_insights) == 1:
                explanation_parts.append(f"featuring {method_insights[0]}")
            else:
                explanation_parts.append(f"combining {' and '.join(method_insights[:2])}")
        
        # Add collaborative insight
        if author_insight:
            explanation_parts.append(f"representing {author_insight}")
        
        # Add temporal context
        if year:
            try:
                year_val = int(year)
                current_year = 2025
                age = current_year - year_val
                if age <= 2:
                    explanation_parts.append("with recent impact")
                elif age <= 5:
                    explanation_parts.append("with sustained influence")
                else:
                    explanation_parts.append("with lasting academic impact")
            except:
                pass
        
        # Combine into coherent explanation
        if len(explanation_parts) >= 3:
            base_explanation = f"{explanation_parts[0]} {explanation_parts[1]} {explanation_parts[2]}"
            if len(explanation_parts) > 3:
                base_explanation += f", {explanation_parts[3]}"
        else:
            base_explanation = " ".join(explanation_parts)
        
        # Add final insight about why this citation count matters
        if citations > 10000:
            impact_note = "indicating exceptional influence in shaping the field"
        elif citations > 5000:
            impact_note = "demonstrating significant scholarly impact"
        elif citations > 1000:
            impact_note = "showing strong academic recognition"
        elif citations > 100:
            impact_note = "reflecting solid scholarly interest"
        elif citations > 0:
            impact_note = "representing emerging academic contribution"
        else:
            # For papers without citation data, focus on other qualities
            if any(term in title_lower for term in ['2024', '2025']) or (year and int(year) >= 2024):
                impact_note = "representing recent contribution with potential for future impact"
            else:
                impact_note = "selected for topical relevance and research quality"
        
        return f"{base_explanation}, {impact_note}."
    
    def _generate_year_explanation(self, paper: Dict[str, Any], rank: int, year: int,
                                 title: str, authors: str, abstract: str) -> str:
        """Generate custom explanation for year-based ranking"""
        
        current_year = 2025
        
        # Extract content characteristics
        content_type = ""
        title_lower = title.lower()
        
        if any(term in title_lower for term in ['survey', 'review', 'overview']):
            content_type = "comprehensive review"
        elif any(term in title_lower for term in ['novel', 'new', 'introducing']):
            content_type = "novel contribution"
        elif any(term in title_lower for term in ['analysis', 'study', 'investigation']):
            content_type = "analytical study"
        elif any(term in title_lower for term in ['framework', 'method', 'approach']):
            content_type = "methodological work"
        elif any(term in title_lower for term in ['application', 'implementation']):
            content_type = "practical application"
        else:
            content_type = "research contribution"
        
        # Analyze research domain from title and abstract
        domain_insights = []
        combined_text = f"{title} {abstract}".lower()
        
        if any(term in combined_text for term in ['neural network', 'deep learning', 'ai', 'artificial intelligence']):
            domain_insights.append('AI/ML')
        if any(term in combined_text for term in ['computer vision', 'image', 'visual']):
            domain_insights.append('computer vision')
        if any(term in combined_text for term in ['natural language', 'nlp', 'text', 'language']):
            domain_insights.append('NLP')
        if any(term in combined_text for term in ['healthcare', 'medical', 'clinical', 'biomedical']):
            domain_insights.append('healthcare')
        if any(term in combined_text for term in ['robotics', 'autonomous', 'control']):
            domain_insights.append('robotics')
        
        # Determine recency significance
        age = current_year - year
        if age <= 1:
            temporal_significance = "presenting the very latest developments"
            recency_value = "cutting-edge insights"
        elif age <= 2:
            temporal_significance = "offering recent breakthroughs"
            recency_value = "current methodologies"
        elif age <= 3:
            temporal_significance = "providing contemporary perspectives"
            recency_value = "modern approaches"
        elif age <= 5:
            temporal_significance = "delivering established recent work"
            recency_value = "proven methodologies"
        else:
            temporal_significance = "contributing foundational insights"
            recency_value = "established principles"
        
        # Build custom explanation
        explanation_parts = []
        
        # Start with ranking and year
        explanation_parts.append(f"Ranked #{rank} as a {year} {content_type}")
        
        # Add domain context
        if domain_insights:
            if len(domain_insights) == 1:
                explanation_parts.append(f"in {domain_insights[0]}")
            else:
                explanation_parts.append(f"bridging {' and '.join(domain_insights[:2])}")
        
        # Add temporal significance
        explanation_parts.append(f"{temporal_significance}")
        
        # Combine and add value proposition
        base_explanation = " ".join(explanation_parts)
        value_prop = f"This work provides {recency_value} essential for understanding current research directions"
        
        return f"{base_explanation}. {value_prop}."
    
    def _generate_enhanced_year_explanation(self, paper: Dict[str, Any], rank: int, year: int,
                                          title: str, authors: str, abstract: str, 
                                          score_components: Dict[str, Any]) -> str:
        """Generate enhanced explanation for year-based ranking with relevance factors"""
        
        current_year = 2025
        
        # Extract scoring components
        recency_score = score_components.get('recency', 0)
        quality_score = score_components.get('quality', 0)
        citation_bonus = score_components.get('citation_bonus', 0)
        venue_bonus = score_components.get('venue_bonus', 0)
        final_score = score_components.get('final', 0)
        
        # Determine primary ranking factor
        primary_factor = ""
        if recency_score >= 0.9 and citation_bonus > 0.1:
            primary_factor = "exceptional recent impact"
        elif recency_score >= 0.9:
            primary_factor = "cutting-edge recency"
        elif citation_bonus > 0.15:
            primary_factor = "high-impact contemporary work"
        elif venue_bonus > 0.1:
            primary_factor = "prestigious venue publication"
        elif quality_score > 0.7:
            primary_factor = "high relevance and quality"
        else:
            primary_factor = "balanced recency and relevance"
        
        # Extract content characteristics
        content_type = ""
        title_lower = title.lower()
        
        if any(term in title_lower for term in ['survey', 'review', 'comprehensive', 'overview']):
            content_type = "comprehensive survey"
        elif any(term in title_lower for term in ['novel', 'new', 'introducing', 'breakthrough']):
            content_type = "novel research"
        elif any(term in title_lower for term in ['analysis', 'study', 'investigation', 'evaluation']):
            content_type = "analytical study"
        elif any(term in title_lower for term in ['framework', 'method', 'approach', 'algorithm']):
            content_type = "methodological contribution"
        elif any(term in title_lower for term in ['application', 'implementation', 'system']):
            content_type = "practical application"
        else:
            content_type = "research work"
        
        # Analyze research domain with enhanced detection
        domain_insights = []
        combined_text = f"{title} {abstract}".lower()
        
        # AI/ML domains
        if any(term in combined_text for term in ['transformer', 'attention', 'bert', 'gpt', 'llm', 'large language model']):
            domain_insights.append('LLM/Transformers')
        elif any(term in combined_text for term in ['neural network', 'deep learning', 'cnn', 'rnn']):
            domain_insights.append('deep learning')
        elif any(term in combined_text for term in ['machine learning', 'ml', 'artificial intelligence', 'ai']):
            domain_insights.append('AI/ML')
        
        # Specific application domains
        if any(term in combined_text for term in ['computer vision', 'image recognition', 'visual', 'opencv']):
            domain_insights.append('computer vision')
        if any(term in combined_text for term in ['natural language processing', 'nlp', 'text analysis', 'sentiment']):
            domain_insights.append('NLP')
        if any(term in combined_text for term in ['healthcare', 'medical', 'clinical', 'biomedical', 'drug']):
            domain_insights.append('healthcare AI')
        if any(term in combined_text for term in ['robotics', 'autonomous', 'control', 'navigation']):
            domain_insights.append('robotics')
        if any(term in combined_text for term in ['quantum', 'blockchain', 'cryptocurrency', 'web3']):
            domain_insights.append('emerging tech')
        
        # Determine temporal context with enhanced granularity
        age = current_year - year
        if age <= 0:
            temporal_context = "cutting-edge 2025 research"
            impact_timeline = "representing the absolute latest developments"
        elif age == 1:
            temporal_context = "very recent 2024 work"
            impact_timeline = "capturing immediate research trends"
        elif age == 2:
            temporal_context = "recent 2023 contribution"
            impact_timeline = "reflecting current methodological advances"
        elif age <= 3:
            temporal_context = "contemporary research"
            impact_timeline = "providing modern technical perspectives"
        elif age <= 5:
            temporal_context = "established recent work"
            impact_timeline = "offering proven contemporary approaches"
        else:
            temporal_context = "foundational work"
            impact_timeline = "contributing established principles"
        
        # Build sophisticated explanation
        explanation_parts = []
        
        # Primary ranking statement
        explanation_parts.append(f"Ranked #{rank} for {primary_factor}")
        
        # Content and domain context
        if domain_insights:
            if len(domain_insights) == 1:
                explanation_parts.append(f"as {year} {content_type} in {domain_insights[0]}")
            else:
                explanation_parts.append(f"as {year} {content_type} bridging {' and '.join(domain_insights[:2])}")
        else:
            explanation_parts.append(f"as {year} {content_type}")
        
        # Add specific ranking insights based on scoring components
        ranking_insights = []
        if citation_bonus > 0.15:
            citations = paper.get('citations', 0)
            try:
                cite_count = int(citations)
                ranking_insights.append(f"with {cite_count} citations demonstrating immediate impact")
            except:
                ranking_insights.append("with notable citation impact")
        
        if venue_bonus > 0.1:
            venue = paper.get('venue', '')
            if venue:
                ranking_insights.append(f"published in prestigious {venue}")
            else:
                ranking_insights.append("from high-quality publication venue")
        
        if quality_score > 0.8:
            ranking_insights.append("featuring exceptional topical relevance")
        elif quality_score > 0.6:
            ranking_insights.append("with strong content quality")
        
        # Combine explanation parts
        base_explanation = " ".join(explanation_parts)
        
        if ranking_insights:
            if len(ranking_insights) == 1:
                base_explanation += f", {ranking_insights[0]}"
            else:
                base_explanation += f", {ranking_insights[0]} and {ranking_insights[1]}"
        
        # Add temporal significance and value proposition
        value_proposition = f"This {temporal_context} is essential for {impact_timeline} in the field"
        
        # Add recommendation based on final score
        if final_score > 0.9:
            recommendation = "representing must-read contemporary research"
        elif final_score > 0.8:
            recommendation = "offering valuable recent insights"
        elif final_score > 0.7:
            recommendation = "providing relevant current perspectives"
        else:
            recommendation = "contributing to the current research landscape"
        
        return f"{base_explanation}. {value_proposition}, {recommendation}."
