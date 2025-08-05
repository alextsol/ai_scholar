from typing import List, Dict, Any, Optional, Set
from ..enums.providers import ProviderType
from ..config.settings import Settings
import logging

logger = logging.getLogger(__name__)

class PaperProcessingUtils:
    
    @staticmethod
    def extract_papers_from_result(result: Any, backend_name: str) -> List[Dict[str, Any]]:
        """
        Extract papers from provider result. Modern providers return lists directly.
        """
        # All modern providers return List[Dict[str, Any]] directly
        if isinstance(result, list):
            papers = result
        else:
            # Fallback for unexpected format
            return []
        
        if not isinstance(papers, list) or not all(isinstance(paper, dict) for paper in papers):
            return []
        
        # Ensure source is set
        for paper in papers:
            paper['source'] = backend_name
        
        return papers
    
    @staticmethod
    def filter_papers_by_year(papers: List[Dict[str, Any]], 
                              min_year: Optional[int], max_year: Optional[int]) -> List[Dict[str, Any]]:
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
    
    @staticmethod
    def remove_duplicates(papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        unique = []
        
        for paper in papers:
            title = paper.get('title', '').lower().strip()
            if title and title not in seen:
                seen.add(title)
                unique.append(paper)
        
        return unique
    
    @staticmethod
    def pre_filter_papers(papers: List[Dict[str, Any]], query: str, provider: str) -> List[Dict[str, Any]]:
        if not papers:
            return papers
        
        filtered = []
        query_words = set(query.lower().split())
        
        for paper in papers:
            try:
                title = PaperProcessingUtils._safe_string_conversion(paper.get('title', ''))
                authors = PaperProcessingUtils._safe_string_conversion(paper.get('authors', ''))
                abstract = PaperProcessingUtils._safe_string_conversion(paper.get('abstract', ''))
                
                if not title or len(title) < 10:
                    continue
                if not authors or authors.lower() in ['unknown', 'n/a', 'no authors']:
                    continue
                
                paper['title'] = title
                paper['authors'] = authors
                paper['abstract'] = abstract
                
                relevance_score = PaperProcessingUtils._calculate_relevance_score(paper, query_words)
                quality_score = PaperProcessingUtils._calculate_quality_score(paper)
                
                combined_score = (relevance_score * 0.7) + (quality_score * 0.3)
                paper['_pre_filter_score'] = combined_score
                
                if combined_score > Settings.PRE_FILTER_MIN_SCORE:
                    filtered.append(paper)
                    
            except Exception:
                continue
        
        filtered.sort(key=lambda x: x.get('_pre_filter_score', 0), reverse=True)
        max_per_provider = Settings.MAX_PER_PROVIDER_AFTER_FILTER
        return filtered[:max_per_provider]
    
    @staticmethod
    def fast_pre_rank(papers: List[Dict[str, Any]], query: str, target_count: int) -> List[Dict[str, Any]]:
        if len(papers) <= target_count:
            return papers
        
        query_words = set(query.lower().split())
        
        for paper in papers:
            score = 0.0
            
            relevance = PaperProcessingUtils._calculate_relevance_score(paper, query_words)
            score += relevance * 0.5
            
            quality = PaperProcessingUtils._calculate_quality_score(paper)
            score += quality * 0.3
            
            citations = paper.get('citations', 0)
            if citations and citations != 'N/A':
                try:
                    cite_count = int(citations)
                    import math
                    citation_score = min(math.log10(cite_count + 1) / 3.0, 1.0)
                    score += citation_score * 0.2
                except:
                    pass
            
            paper['_fast_rank_score'] = score
        
        papers.sort(key=lambda x: x.get('_fast_rank_score', 0), reverse=True)
        return papers[:target_count]
    
    @staticmethod
    def cleanup_temporary_fields(papers: List[Dict[str, Any]]) -> None:
        temp_fields = ['_pre_filter_score', '_fast_rank_score', '_quality_score', 
                      '_year_relevance_score', '_year_score_components']
        for paper in papers:
            for field in temp_fields:
                paper.pop(field, None)
    
    @staticmethod
    def merge_ranked_with_details(ranked_papers: List[Dict[str, Any]], 
                                  all_papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        merged = []
        
        for ranked_paper in ranked_papers:
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
    
    @staticmethod
    def _safe_string_conversion(value: Any) -> str:
        if isinstance(value, list):
            return ' '.join(str(v) for v in value if v is not None)
        elif value is None:
            return ''
        return str(value).strip()
    
    @staticmethod
    def _calculate_relevance_score(paper: Dict[str, Any], query_words: Set[str]) -> float:
        score = 0.0
        
        title = PaperProcessingUtils._safe_string_conversion(paper.get('title', '')).lower()
        abstract = PaperProcessingUtils._safe_string_conversion(paper.get('abstract', '')).lower()
        
        if title:
            title_words = set(title.split())
            title_matches = len(query_words.intersection(title_words))
            if title_matches > 0:
                score += (title_matches / len(query_words)) * 0.6
        
        if abstract:
            abstract_words = set(abstract.split())
            abstract_matches = len(query_words.intersection(abstract_words))
            if abstract_matches > 0:
                score += (abstract_matches / len(query_words)) * 0.4
        
        query_text = ' '.join(query_words)
        if query_text in title:
            score += 0.3
        elif query_text in abstract:
            score += 0.2
        
        return min(score, 1.0)
    
    @staticmethod
    def _calculate_quality_score(paper: Dict[str, Any]) -> float:
        score = 0.0
        
        if paper.get('doi'):
            score += 0.3
        
        if paper.get('url'):
            score += 0.2
        
        abstract = PaperProcessingUtils._safe_string_conversion(paper.get('abstract', ''))
        
        if abstract and len(abstract) > 100:
            score += 0.3
        elif abstract and len(abstract) > 50:
            score += 0.2
        
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
        
        year = paper.get('year')
        if year and year != 'Unknown':
            try:
                pub_year = int(year)
                current_year = 2025
                if current_year - pub_year <= 10:
                    score += 0.1
            except:
                pass
        
        return min(score, 1.0)
