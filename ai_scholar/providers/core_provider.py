from typing import List, Optional, Dict, Any
from ..interfaces.search_interface import ISearchProvider
from ..utils.exceptions import RateLimitError, APIUnavailableError, SearchError, AuthenticationError, NetworkError, TimeoutError
from ..utils.error_handler import ErrorHandler, handle_provider_error
import requests
import time
import logging

logger = logging.getLogger(__name__)

class COREProvider(ISearchProvider):
    """CORE (COnnecting REpositories) search provider implementation"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://api.core.ac.uk/v3"
        self.search_url = f"{self.base_url}/search/works"
        # Try alternative endpoints if main fails
        self.alt_search_url = "https://core.ac.uk/api-v2/articles/search"  # v2 fallback
        self.rate_limit_delay = 2.0  # Slower rate to avoid rate limits
        self.last_request_time = 0
    
    @handle_provider_error("CORE")
    def search(self, query: str, limit: int, min_year: Optional[int] = None, max_year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search CORE for papers"""
        if not self.validate_query(query):
            raise SearchError(f"Invalid query: {query}", "Please enter a valid search query with at least 3 characters.")
        
        # Quick rate limit check - if we just made a request, wait a bit
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < 1.0:
            time.sleep(1.0 - time_since_last)
        
        # Try v3 API first
        try:
            results = self._search_v3(query, limit, min_year, max_year)
            if results:
                return results
        except RateLimitError:
            # If v3 is rate limited, try v2
            logger.info("CORE v3 rate limited, trying v2 API")
        except APIUnavailableError as e:
            # If v3 is unavailable, try v2
            logger.info(f"CORE v3 unavailable ({e}), trying v2 API")
        
        # Fallback to v2 API
        return self._search_v2(query, limit, min_year, max_year)
    
    def _search_v3(self, query: str, limit: int, min_year: Optional[int] = None, max_year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search using CORE v3 API"""
        # Build better search query
        search_terms = query.strip()
        
        # Build search parameters with better filtering
        params = {
            'q': search_terms,
            'limit': min(limit * 2, 100),  # Get more results to filter
            'offset': 0,
            'sort': 'relevance'
        }
        
        # Add year filters if specified
        if min_year or max_year:
            year_filter = self._build_year_filter(min_year, max_year)
            if year_filter:
                params['q'] = f"{params['q']} AND {year_filter}"
        else:
            # Default to more recent papers for better quality
            from datetime import datetime
            current_year = datetime.now().year
            recent_filter = self._build_year_filter(current_year - 15, None)  # Last 15 years
            if recent_filter:
                params['q'] = f"{params['q']} AND {recent_filter}"
        
        # Make request
        response = self._make_request(self.search_url, params)
        
        if response and response.status_code == 200:
            data = response.json()
            papers = data.get('results', [])
            if not papers:
                logger.info(f"CORE v3 returned no results for query: {query}")
                return []
            
            standardized = self._standardize_papers_v3(papers)
            
            # Apply quality filtering
            quality_papers = self._filter_quality_papers(standardized)
            
            logger.info(f"CORE v3 found {len(quality_papers)} quality papers")
            return quality_papers[:limit]
        
        logger.warning("CORE v3 API request failed or returned non-200 status")
        raise APIUnavailableError("CORE", message="CORE v3 API request failed")
    
    def _search_v2(self, query: str, limit: int, min_year: Optional[int] = None, max_year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search using CORE v2 API as fallback"""
        # Build search parameters for v2
        params = {
            'query': query.strip(),
            'page': 1,
            'pageSize': min(limit, 100),
            'apiKey': self.api_key if self.api_key else ''
        }
        
        # Make request to v2 endpoint
        response = self._make_request(self.alt_search_url, params)
        
        if response and response.status_code == 200:
            data = response.json()
            papers = data.get('data', [])
            if not papers:
                logger.info(f"CORE v2 returned no results for query: {query}")
                return []
            
            standardized = self._standardize_papers_v2(papers)
            logger.info(f"CORE v2 found {len(standardized)} papers")
            return standardized
        
        logger.warning("CORE v2 API request failed or returned non-200 status")
        raise APIUnavailableError("CORE", message="CORE v2 API request failed")
    
    def get_provider_name(self) -> str:
        return "CORE"
    
    def is_available(self) -> bool:
        """Check if CORE API is available"""
        try:
            headers = self._get_headers()
            
            # Try main v3 API
            test_response = requests.get(
                self.search_url,
                params={'q': 'test', 'limit': 1},
                headers=headers,
                timeout=15
            )
            
            # Consider 200, 401 (needs auth), and even 500 (service exists but has issues) as "available"
            if test_response.status_code in [200, 401]:
                return True
            
            # If v3 fails, try v2 API as fallback
            if hasattr(self, 'alt_search_url'):
                alt_response = requests.get(
                    self.alt_search_url,
                    params={'query': 'test', 'page': 1, 'pageSize': 1},
                    headers=headers,
                    timeout=15
                )
                return alt_response.status_code in [200, 401]
            
            return False
            
        except:
            return False
    
    def validate_query(self, query: str) -> bool:
        """Validate CORE query"""
        if not query or not query.strip():
            return False
        return len(query.strip()) >= 2
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with API key if available"""
        headers = {
            'User-Agent': 'AI-Scholar/1.0',
            'Accept': 'application/json'
        }
        
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        return headers
    
    def _build_year_filter(self, min_year: Optional[int], max_year: Optional[int]) -> str:
        """Build year filter for CORE query"""
        if min_year and max_year:
            return f"yearPublished:[{min_year} TO {max_year}]"
        elif min_year:
            return f"yearPublished:[{min_year} TO *]"
        elif max_year:
            return f"yearPublished:[* TO {max_year}]"
        return ""
    
    def _make_request(self, url: str, params: Dict[str, Any]) -> Optional[requests.Response]:
        """Make request to CORE API with better rate limiting"""
        max_retries = 2  # Reduced retries to avoid long waits
        base_delay = 3    # Longer base delay
        
        for attempt in range(max_retries):
            try:
                # Better rate limiting - ensure minimum time between requests
                current_time = time.time()
                time_since_last = current_time - self.last_request_time
                if time_since_last < self.rate_limit_delay:
                    time.sleep(self.rate_limit_delay - time_since_last)
                
                # Additional delay for retries
                if attempt > 0:
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
                
                headers = self._get_headers()
                
                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=30
                )
                
                self.last_request_time = time.time()
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # Rate limited
                    retry_after = response.headers.get('Retry-After', '300')  # Default 5 minutes for CORE
                    retry_seconds = int(retry_after) if retry_after.isdigit() else 300
                    
                    # Raise RateLimitError with proper retry time
                    raise RateLimitError("CORE", retry_after_seconds=retry_seconds)
                        
                elif response.status_code in [401, 403]:
                    raise AuthenticationError("CORE", "Invalid API key or insufficient permissions")
                elif response.status_code == 500:
                    # Server error - might be temporary
                    if attempt == max_retries - 1:
                        raise APIUnavailableError("CORE", "Server error (HTTP 500)")
                    continue
                else:
                    if attempt == max_retries - 1:
                        raise APIUnavailableError("CORE", f"HTTP {response.status_code}")
                    
            except requests.exceptions.Timeout:
                if attempt == max_retries - 1:
                    raise TimeoutError("CORE", "Request timed out after 30 seconds")
            except requests.exceptions.ConnectionError:
                if attempt == max_retries - 1:
                    raise NetworkError("CORE", "Connection failed")
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise APIUnavailableError("CORE", f"Request failed: {str(e)}")
        
        # If we get here, all retries failed
        raise APIUnavailableError("CORE", "All retry attempts failed")
    
    def _standardize_papers_v3(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Standardize papers to match expected schema"""
        standardized = []
        
        for paper in papers:
            try:
                # Handle title
                title = paper.get('title', 'No title')
                
                # Handle authors
                authors_list = paper.get('authors', [])
                if isinstance(authors_list, list):
                    author_names = []
                    for author in authors_list:
                        if isinstance(author, dict):
                            name = author.get('name', '')
                        elif isinstance(author, str):
                            name = author
                        else:
                            continue
                        if name:
                            author_names.append(name)
                    authors_str = ', '.join(author_names) if author_names else 'Unknown'
                else:
                    authors_str = str(authors_list) if authors_list else 'Unknown'
                
                # Handle year
                year = paper.get('yearPublished', 'Unknown')
                if not year or year == 0:
                    # Try to extract from date fields
                    pub_date = paper.get('publishedDate') or paper.get('depositedDate')
                    if pub_date:
                        try:
                            year = int(pub_date.split('-')[0])
                        except:
                            year = 'Unknown'
                
                # Handle abstract
                abstract = paper.get('abstract', '')
                
                # Handle URLs
                download_url = paper.get('downloadUrl', '')
                fulltext_url = paper.get('fulltextUrls', {}).get('pdf', '')
                url = download_url or fulltext_url or ''
                
                # Handle DOI
                doi = paper.get('doi', '')
                if doi and not url:
                    url = f"https://doi.org/{doi}"
                
                # Handle citations (not typically available in CORE)
                # CORE doesn't provide citation counts, so we'll use 'N/A' or estimate based on age
                citation_count = paper.get('citationCount', 'N/A')
                if citation_count == 'N/A' or citation_count == 0:
                    # For display purposes, indicate that citation data is not available
                    citation_count = 'N/A'
                
                # Handle repository/publisher info
                repositories = paper.get('repositories', [])
                repository_name = repositories[0].get('name', '') if repositories else ''
                
                standardized_paper = {
                    'title': title,
                    'authors': authors_str,
                    'year': year,
                    'abstract': abstract,
                    'url': url,
                    'citations': citation_count,
                    'source': 'core',
                    'provider': self.get_provider_name(),
                    'doi': doi,
                    'repository': repository_name,
                    'language': paper.get('language', {}).get('code', ''),
                    'subjects': paper.get('subjects', []),
                    'publisher': paper.get('publisher', ''),
                    'journal': paper.get('journals', [{}])[0].get('title', '') if paper.get('journals') else '',
                    'oai_id': paper.get('oai', ''),
                    'core_id': paper.get('id', ''),
                    'published_date': paper.get('publishedDate', ''),
                    'deposited_date': paper.get('depositedDate', '')
                }
                
                standardized.append(standardized_paper)
                
            except Exception as e:
                continue
        
        return standardized
    
    def _filter_quality_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter papers for better quality"""
        quality_papers = []
        
        for paper in papers:
            # Skip papers without proper titles
            title = paper.get('title', '').strip()
            if not title or len(title) < 10:
                continue
                
            # Skip papers without authors
            authors = paper.get('authors', '')
            if not authors or authors == 'Unknown':
                continue
            
            # Skip papers without abstracts (usually lower quality)
            abstract = paper.get('abstract', '').strip()
            if not abstract or len(abstract) < 50:
                continue
            
            # Prefer papers with DOIs (usually higher quality)
            doi = paper.get('doi', '')
            has_doi = bool(doi)
            
            # Prefer papers with URLs (accessible)
            url = paper.get('url', '')
            has_url = bool(url)
            
            # Skip if no DOI and no URL
            if not has_doi and not has_url:
                continue
                
            # Add quality score for sorting
            quality_score = 0
            if has_doi:
                quality_score += 2
            if has_url:
                quality_score += 1
            if len(abstract) > 200:
                quality_score += 1
                
            paper['_quality_score'] = quality_score
            quality_papers.append(paper)
        
        # Sort by quality score and return
        quality_papers.sort(key=lambda p: p.get('_quality_score', 0), reverse=True)
        
        # Remove the quality score field
        for paper in quality_papers:
            paper.pop('_quality_score', None)
            
        return quality_papers

    def get_paper_by_core_id(self, core_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific paper by CORE ID"""
        if not core_id:
            return None
        
        try:
            url = f"{self.base_url}/works/{core_id}"
            headers = self._get_headers()
            time.sleep(self.rate_limit_delay)
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                paper_data = response.json()
                if paper_data:
                    return self._standardize_papers_v3([paper_data])[0]
            
        except Exception as e:
            pass
        
        return None

    def _standardize_papers_v2(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Standardize papers from CORE v2 API to match expected schema"""
        standardized = []
        
        for paper in papers:
            try:
                # Handle title
                title = paper.get('title', 'No title')
                
                # Handle authors (v2 format is different)
                authors_list = paper.get('authors', [])
                if isinstance(authors_list, list):
                    # In v2, authors might be strings or objects
                    author_names = []
                    for author in authors_list:
                        if isinstance(author, str):
                            author_names.append(author)
                        elif isinstance(author, dict):
                            name = author.get('name', '') or f"{author.get('firstname', '')} {author.get('surname', '')}".strip()
                            if name:
                                author_names.append(name)
                    authors_str = ', '.join(author_names) if author_names else 'Unknown'
                else:
                    authors_str = str(authors_list) if authors_list else 'Unknown'
                
                # Handle year
                year = paper.get('year', 'Unknown')
                if not year:
                    # Try to extract from datePublished
                    date_pub = paper.get('datePublished')
                    if date_pub:
                        try:
                            year = int(date_pub.split('-')[0])
                        except:
                            year = 'Unknown'
                
                # Handle abstract
                abstract = paper.get('description', '') or paper.get('abstract', '')
                
                # Handle URLs - v2 API structure
                download_url = paper.get('downloadUrl', '')
                fulltext_urls = paper.get('fulltextUrls', [])
                pdf_url = fulltext_urls[0] if fulltext_urls else ''
                url = download_url or pdf_url or ''
                
                # Handle DOI
                doi = paper.get('doi', '') or paper.get('identifiers', {}).get('doi', '')
                if doi and not url:
                    url = f"https://doi.org/{doi}"
                
                # Handle citations - v2 might have citedBy info
                citation_count = paper.get('citedBy', 'N/A')
                if isinstance(citation_count, list):
                    citation_count = len(citation_count)
                elif citation_count == 'N/A' or citation_count == 0:
                    citation_count = 'N/A'
                
                # Handle repository info
                repositories = paper.get('repositories', [])
                repository_name = repositories[0].get('name', '') if repositories else ''
                
                standardized_paper = {
                    'title': title,
                    'authors': authors_str,
                    'year': year,
                    'abstract': abstract,
                    'url': url,
                    'citations': citation_count,
                    'source': 'core',
                    'provider': self.get_provider_name(),
                    'doi': doi,
                    'repository': repository_name,
                    'language': paper.get('language', ''),
                    'subjects': paper.get('subjects', []),
                    'publisher': paper.get('publisher', ''),
                    'journal': paper.get('journal', ''),
                    'oai_id': paper.get('oai', ''),
                    'core_id': paper.get('id', ''),
                    'published_date': paper.get('datePublished', ''),
                    'deposited_date': paper.get('depositedDate', '')
                }
                
                standardized.append(standardized_paper)
                
            except Exception as e:
                continue
        
        return standardized
