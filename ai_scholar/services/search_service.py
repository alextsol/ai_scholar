from typing import List, Optional, Dict, Any
from ..interfaces.search_interface import ISearchProvider
from ..models.search_request import SearchRequest
from ..models.search_result import SearchResult
from ..models.paper import Paper
from ..cache import get_cache_key, get_cached_result, cache_result, cleanup_expired_cache
from ..enums import ProviderType
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests
import time
import random

class SearchService:
    """Service for handling paper search operations"""
    
    def __init__(self, search_providers: Dict[str, ISearchProvider], default_backend: str = 'crossref'):
        self.search_providers = search_providers
        self.default_backend = default_backend
    
    def search_papers(self, search_request: SearchRequest) -> SearchResult:
        """
        Search for papers using the specified or default provider
        
        Args:
            search_request: SearchRequest object with search parameters
            
        Returns:
            SearchResult with papers and metadata
        """
        cleanup_expired_cache()
        
        # Handle multiple backends or default to single backend
        backends = search_request.backends or [self.default_backend]
        if not backends:
            backends = [self.default_backend]
        
        # For now, use the first backend (can be enhanced later for multi-backend search)
        backend = backends[0]
        
        if backend not in self.search_providers:
            raise ValueError(f"Unknown backend '{backend}' specified")
        
        cache_key = get_cache_key(
            search_request.query, 
            search_request.limit, 
            backend, 
            search_request.min_year, 
            search_request.max_year
        )
        
        cached_result = get_cached_result(cache_key)
        if cached_result is not None:
            # Convert cached dictionary papers to Paper objects
            cached_paper_objects = []
            for paper_dict in cached_result:
                if isinstance(paper_dict, dict):
                    paper_obj = Paper(
                        title=paper_dict.get('title', ''),
                        authors=paper_dict.get('authors', ''),
                        abstract=paper_dict.get('abstract', ''),
                        year=paper_dict.get('year'),
                        url=paper_dict.get('url', ''),
                        citations=paper_dict.get('citations'),
                        source=paper_dict.get('source', ''),
                        published=paper_dict.get('published', '')
                    )
                    cached_paper_objects.append(paper_obj)
            
            return SearchResult(
                papers=cached_paper_objects,
                query=search_request.query,
                total_found=len(cached_paper_objects),
                processing_time=0.0,
                ranking_mode=search_request.ranking_mode,
                backends_used=[backend],
                cache_hit=True
            )
        
        start_time = time.time()
        papers = self._search_with_retry(
            backend, 
            search_request.query, 
            search_request.limit,
            search_request.min_year,
            search_request.max_year
        )
        search_time = time.time() - start_time
        
        if papers and not isinstance(papers, str):
            cache_result(cache_key, papers)
        
        if isinstance(papers, str) and papers.startswith("Error:"):
            raise RuntimeError(papers)
        
        if not papers:
            papers = []
        
        # Convert dictionary papers to Paper objects
        paper_objects = []
        for paper_dict in papers:
            if isinstance(paper_dict, dict):
                paper_obj = Paper(
                    title=paper_dict.get('title', ''),
                    authors=paper_dict.get('authors', ''),
                    abstract=paper_dict.get('abstract', ''),
                    year=paper_dict.get('year'),
                    url=paper_dict.get('url', ''),
                    citations=paper_dict.get('citations'),
                    source=paper_dict.get('source', ''),
                    published=paper_dict.get('published', '')
                )
                paper_objects.append(paper_obj)
        
        return SearchResult(
            papers=paper_objects,
            query=search_request.query,
            total_found=len(paper_objects),
            processing_time=search_time,
            ranking_mode=search_request.ranking_mode,
            backends_used=[backend],
            cache_hit=False
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=5, max=120),
        retry=retry_if_exception_type((requests.exceptions.RequestException,)),
        reraise=True
    )
    def _search_with_retry(self, backend: str, query: str, limit: int, 
                          min_year: Optional[int] = None, max_year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search with retry logic for reliability"""
        
        if backend == ProviderType.SEMANTIC_SCHOLAR.value:
            time.sleep(random.uniform(2, 5))
        
        provider = self.search_providers[backend]
        
        if not provider.is_available():
            raise RuntimeError(f"Provider {backend} is not available")
        
        return provider.search(query, limit, min_year, max_year)
    
    def get_available_backends(self) -> List[str]:
        """Get list of available search backends"""
        return [name for name, provider in self.search_providers.items() 
                if provider.is_available()]
    
    def validate_search_request(self, search_request: SearchRequest) -> bool:
        """Validate a search request"""
        if not search_request.query or not search_request.query.strip():
            return False
        
        # Handle multiple backends or default to single backend
        backends = search_request.backends or [self.default_backend]
        if not backends:
            backends = [self.default_backend]
        
        # For now, validate the first backend (can be enhanced later)
        backend = backends[0]
        if backend not in self.search_providers:
            return False
        
        backend = backend or self.default_backend
        provider = self.search_providers[backend]
        
        return provider.validate_query(search_request.query)
    
    def get_provider_info(self, backend: str) -> Dict[str, Any]:
        """Get information about a specific provider"""
        if backend not in self.search_providers:
            return {}
        
        provider = self.search_providers[backend]
        return {
            'name': provider.get_provider_name(),
            'available': provider.is_available(),
            'backend_key': backend
        }
