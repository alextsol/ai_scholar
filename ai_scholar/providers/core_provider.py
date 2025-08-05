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
        self.discovery_url = f"{self.base_url}/discover"
        self.alt_search_url = "https://core.ac.uk/api-v2/search"  # v2 fallback
        
        self.rate_limit_delay = 2.0 
        self.last_request_time = 0
    
    @handle_provider_error("CORE")
    def search(self, query: str, limit: int, min_year: Optional[int] = None, max_year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search CORE for papers using multiple endpoint fallbacks"""
        if not self.validate_query(query):
            raise SearchError(f"Invalid query: {query}", "Please enter a valid search query with at least 3 characters.")
        
        self._apply_rate_limit()
        
        # Try endpoints in order of preference
        search_methods = [
            ("Discovery API", self._search_discovery),
            ("Search API v3", self._search_v3), 
            ("Search API v2", self._search_v2)
        ]
        
        for endpoint_name, search_method in search_methods:
            try:
                logger.info(f"CORE: Trying {endpoint_name}")
                results = search_method(query, limit, min_year, max_year)
                if results:
                    logger.info(f"CORE: {endpoint_name} succeeded with {len(results)} results")
                    return results
                logger.info(f"CORE: {endpoint_name} returned no results")
            except RateLimitError:
                logger.warning(f"CORE: {endpoint_name} rate limited")
                raise 
            except Exception as e:
                logger.warning(f"CORE: {endpoint_name} failed: {str(e)}")
                continue
        
        logger.warning("CORE: All endpoints failed, returning empty results")
        return []

    def _apply_rate_limit(self):
        """Apply rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < 1.0:
            time.sleep(1.0 - time_since_last)

    def _search_discovery(self, query: str, limit: int, min_year: Optional[int] = None, max_year: Optional[int] = None) -> List[Dict[str, Any]]:
        params = {
            'q': query.strip(),
            'limit': min(limit, 100),
            'offset': 0
        }
        
        if min_year or max_year:
            year_filter = self._build_year_filter(min_year, max_year)
            if year_filter:
                params['q'] = f"{params['q']} AND {year_filter}"
        
        response = self._make_request(self.discovery_url, params)
        
        if response and response.status_code == 200:
            data = response.json()
            papers = data.get('results', [])
            if papers:
                standardized = self._standardize_papers_v3(papers)
                quality_papers = self._filter_quality_papers(standardized)
                return quality_papers[:limit]
        
        return []

    def _search_v3(self, query: str, limit: int, min_year: Optional[int] = None, max_year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search using CORE v3 API"""
        params = {
            'q': self._build_search_query(query.strip(), min_year, max_year),
            'limit': min(limit * 2, 100),  # Get more results to filter
            'offset': 0,
            'sort': 'relevance'
        }
        
        response = self._make_request(self.search_url, params)
        return self._process_v3_response(response, query, limit)

    def _search_v2(self, query: str, limit: int, min_year: Optional[int] = None, max_year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search using CORE v2 API as fallback"""
        params = {
            'query': query.strip(),
            'page': 1,
            'pageSize': min(limit, 100),
            'apiKey': self.api_key if self.api_key else ''
        }
        
        response = self._make_request(self.alt_search_url, params)
        return self._process_v2_response(response, query)

    def _build_search_query(self, query: str, min_year: Optional[int] = None, max_year: Optional[int] = None) -> str:
        """Build optimized search query with year filters"""
        if min_year or max_year:
            year_filter = self._build_year_filter(min_year, max_year)
            if year_filter:
                return f"{query} AND {year_filter}"
        else:
            # Default to recent papers for better quality
            from datetime import datetime
            current_year = datetime.now().year
            recent_filter = self._build_year_filter(current_year - 15, None)  # Last 15 years
            if recent_filter:
                return f"{query} AND {recent_filter}"
        return query

    def _process_v3_response(self, response, query: str, limit: int) -> List[Dict[str, Any]]:
        """Process v3 API response"""
        if not response or response.status_code != 200:
            logger.warning("CORE v3 API request failed or returned non-200 status")
            raise APIUnavailableError("CORE", message="CORE v3 API request failed")
        
        data = response.json()
        papers = data.get('results', [])
        if not papers:
            logger.info(f"CORE v3 returned no results for query: {query}")
            return []
        
        standardized = self._standardize_papers_v3(papers)
        quality_papers = self._filter_quality_papers(standardized)
        logger.info(f"CORE v3 found {len(quality_papers)} quality papers")
        return quality_papers[:limit]

    def _process_v2_response(self, response, query: str) -> List[Dict[str, Any]]:
        """Process v2 API response"""
        if not response or response.status_code != 200:
            logger.warning("CORE v2 API request failed or returned non-200 status")
            raise APIUnavailableError("CORE", message="CORE v2 API request failed")
        
        data = response.json()
        papers = data.get('data', [])
        if not papers:
            logger.info(f"CORE v2 returned no results for query: {query}")
            return []
        
        standardized = self._standardize_papers_v2(papers)
        logger.info(f"CORE v2 found {len(standardized)} papers")
        return standardized
    
    def get_provider_name(self) -> str:
        return "CORE"
    
    def is_available(self) -> bool:
        """Check if CORE API is available"""
        try:
            headers = self._get_headers()
            test_params = {'q': 'test', 'limit': 1}
            
            # Try main v3 API first
            response = requests.get(self.search_url, params=test_params, headers=headers, timeout=15)
            if response.status_code in [200, 401]:
                return True
            
            # Fallback to v2 API
            v2_params = {'query': 'test', 'page': 1, 'pageSize': 1}
            response = requests.get(self.alt_search_url, params=v2_params, headers=headers, timeout=15)
            return response.status_code in [200, 401]
            
        except:
            return False
    
    def validate_query(self, query: str) -> bool:
        if not query or not query.strip():
            return False
        return len(query.strip()) >= 2
    
    def _get_headers(self) -> Dict[str, str]:
        headers = {
            'User-Agent': 'AI-Scholar/1.0',
            'Accept': 'application/json'
        }
        
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        return headers
    
    def _build_year_filter(self, min_year: Optional[int], max_year: Optional[int]) -> str:
        if min_year and max_year:
            return f"yearPublished:[{min_year} TO {max_year}]"
        elif min_year:
            return f"yearPublished:[{min_year} TO *]"
        elif max_year:
            return f"yearPublished:[* TO {max_year}]"
        return ""
    
    def _make_request(self, url: str, params: Dict[str, Any]) -> Optional[requests.Response]:
        max_retries = 2  # Reduced retries to avoid long waits
        base_delay = 3    # Longer base delay
        
        for attempt in range(max_retries):
            try:
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
                    # Auth error - log and continue with other endpoints
                    logger.warning(f"CORE: Authentication issue (HTTP {response.status_code})")
                    return None
                elif response.status_code == 404:
                    # Endpoint not found - try other endpoints
                    logger.warning(f"CORE: Endpoint not found (HTTP 404) for {url}")
                    return None
                elif response.status_code == 500:
                    # Server error - might be temporary
                    logger.warning(f"CORE: Server error (HTTP 500)")
                    if attempt == max_retries - 1:
                        return None
                    continue
                else:
                    logger.warning(f"CORE: HTTP {response.status_code} for {url}")
                    if attempt == max_retries - 1:
                        return None
                    
            except requests.exceptions.Timeout:
                logger.warning(f"CORE: Request timeout for {url}")
                if attempt == max_retries - 1:
                    return None
            except requests.exceptions.ConnectionError:
                logger.warning(f"CORE: Connection error for {url}")
                if attempt == max_retries - 1:
                    return None
            except requests.exceptions.RequestException as e:
                logger.warning(f"CORE: Request error for {url}: {str(e)}")
                if attempt == max_retries - 1:
                    return None
        
        # If we get here, all retries failed
        logger.warning(f"CORE: All retry attempts failed for {url}")
        return None
    
    def _standardize_papers_v3(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Standardize papers from v3 API to match expected schema"""
        return [self._standardize_single_paper_v3(paper) for paper in papers if self._is_valid_paper(paper)]

    def _standardize_papers_v2(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Standardize papers from v2 API to match expected schema"""
        return [self._standardize_single_paper_v2(paper) for paper in papers if self._is_valid_paper(paper)]

    def _is_valid_paper(self, paper: Dict[str, Any]) -> bool:
        """Check if paper has minimum required fields"""
        return paper.get('title') and paper.get('title').strip()

    def _extract_authors(self, authors_data: Any, is_v2: bool = False) -> str:
        """Extract and format author names from different API formats"""
        if not authors_data:
            return 'Unknown'
            
        if isinstance(authors_data, list):
            author_names = []
            for author in authors_data:
                if isinstance(author, dict):
                    if is_v2:
                        name = author.get('name', '') or f"{author.get('firstname', '')} {author.get('surname', '')}".strip()
                    else:
                        name = author.get('name', '')
                elif isinstance(author, str):
                    name = author
                else:
                    continue
                if name:
                    author_names.append(name)
            return ', '.join(author_names) if author_names else 'Unknown'
        
        return str(authors_data) if authors_data else 'Unknown'

    def _extract_year(self, paper: Dict[str, Any], is_v2: bool = False) -> str:
        """Extract publication year from different API formats"""
        if is_v2:
            year = paper.get('year', 'Unknown')
            if not year:
                date_pub = paper.get('datePublished')
                if date_pub:
                    try:
                        year = int(date_pub.split('-')[0])
                    except:
                        year = 'Unknown'
        else:
            year = paper.get('yearPublished', 'Unknown')
            if not year or year == 0:
                pub_date = paper.get('publishedDate') or paper.get('depositedDate')
                if pub_date:
                    try:
                        year = int(pub_date.split('-')[0])
                    except:
                        year = 'Unknown'
        return year

    def _extract_url_and_doi(self, paper: Dict[str, Any], is_v2: bool = False) -> tuple:
        """Extract URL and DOI from paper data"""
        if is_v2:
            download_url = paper.get('downloadUrl', '')
            fulltext_urls = paper.get('fulltextUrls', [])
            pdf_url = fulltext_urls[0] if fulltext_urls else ''
            url = download_url or pdf_url or ''
            doi = paper.get('doi', '') or paper.get('identifiers', {}).get('doi', '')
        else:
            download_url = paper.get('downloadUrl', '')
            fulltext_url = paper.get('fulltextUrls', {}).get('pdf', '')
            url = download_url or fulltext_url or ''
            doi = paper.get('doi', '')
        
        if doi and not url:
            url = f"https://doi.org/{doi}"
        
        return url, doi

    def _standardize_single_paper_v3(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize a single paper from v3 API"""
        try:
            title = paper.get('title', 'No title')
            authors_str = self._extract_authors(paper.get('authors', []))
            year = self._extract_year(paper)
            abstract = paper.get('abstract', '')
            url, doi = self._extract_url_and_doi(paper)
            
            repositories = paper.get('repositories', [])
            repository_name = repositories[0].get('name', '') if repositories else ''
            
            return {
                'title': title,
                'authors': authors_str,
                'year': year,
                'abstract': abstract,
                'url': url,
                'citations': 'N/A',  # CORE doesn't provide citation counts
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
        except Exception:
            return None

    def _standardize_single_paper_v2(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize a single paper from v2 API"""
        try:
            title = paper.get('title', 'No title')
            authors_str = self._extract_authors(paper.get('authors', []), is_v2=True)
            year = self._extract_year(paper, is_v2=True)
            abstract = paper.get('description', '') or paper.get('abstract', '')
            url, doi = self._extract_url_and_doi(paper, is_v2=True)
            
            # Handle citations for v2
            citation_count = paper.get('citedBy', 'N/A')
            if isinstance(citation_count, list):
                citation_count = len(citation_count)
            elif citation_count == 'N/A' or citation_count == 0:
                citation_count = 'N/A'
            
            repositories = paper.get('repositories', [])
            repository_name = repositories[0].get('name', '') if repositories else ''
            
            return {
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
        except Exception:
            return None
    
    def _filter_quality_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        quality_papers = []
        
        for paper in papers:
            # Skip papers without proper titles
            title = paper.get('title', '').strip()
            if not title or len(title) < 10:
                continue
                
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
