from typing import List, Optional, Dict, Any
from ..interfaces.search_interface import ISearchProvider
from ..utils.exceptions import RateLimitError, APIUnavailableError, SearchError
from ..utils.error_handler import ErrorHandler, handle_provider_error
import requests
import time
import logging

logger = logging.getLogger(__name__)

class CrossRefProvider(ISearchProvider):
    """CrossRef search provider implementation"""
    
    def __init__(self, api_key: Optional[str] = None, mailto: Optional[str] = None):
        self.api_key = api_key
        self.mailto = mailto or "support@ai-scholar.com"
        self.base_url = "https://api.crossref.org/works"
        self.rate_limit_delay = 1.0  # Polite rate limiting
    
    @handle_provider_error("CrossRef")
    def search(self, query: str, limit: int, min_year: Optional[int] = None, max_year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search CrossRef for papers"""
        if not self.validate_query(query):
            raise SearchError(f"Invalid query: {query}", "Please enter a valid search query with at least 3 characters.")

        # Build search parameters with better filtering
        params = {
            'query': query.strip(),
            'rows': min(limit * 2, 500),  # Get 2x results to filter out some
            'sort': 'is-referenced-by-count',  # Sort by citation count for quality
            'order': 'desc'
        }
        
        filters = []
        
        filters.append('type:journal-article')
        
        # Add year filters if specified
        if min_year:
            filters.append(f"from-pub-date:{min_year}")
        if max_year:
            filters.append(f"until-pub-date:{max_year}")
        else:
            # Default to papers from last 20 years for relevance
            from datetime import datetime
            current_year = datetime.now().year
            filters.append(f"from-pub-date:{current_year - 20}")
        
        params['filter'] = ','.join(filters)

        # Make request with rate limiting
        response = self._make_request(params)
        
        if response and response.status_code == 200:
            data = response.json()
            papers = data.get('message', {}).get('items', [])
            standardized = self._standardize_papers(papers)
            
            # Additional quality filtering after standardization
            quality_papers = self._filter_quality_papers(standardized)
            
            # Return only the requested number of results
            return quality_papers[:limit]
        
        # If we get here, something went wrong but didn't raise an exception
        raise APIUnavailableError("CrossRef", message="No response received from CrossRef API")
    
    def get_provider_name(self) -> str:
        return "CrossRef"
    
    def is_available(self) -> bool:
        """Check if CrossRef API is available"""
        try:
            headers = self._get_headers()
            test_response = requests.get(
                self.base_url,
                params={'query': 'test', 'rows': 1},
                headers=headers,
                timeout=10
            )
            return test_response.status_code == 200
        except:
            return False
    
    def validate_query(self, query: str) -> bool:
        """Validate CrossRef query"""
        if not query or not query.strip():
            return False
        return len(query.strip()) >= 2
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with proper user agent"""
        headers = {
            'User-Agent': f'AI-Scholar/1.0 (mailto:{self.mailto})',
            'Accept': 'application/json'
        }
        
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        return headers
    
    def _make_request(self, params: Dict[str, Any]) -> Optional[requests.Response]:
        """Make request to CrossRef API with rate limiting and proper error handling"""
        max_retries = 3
        base_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Rate limiting delay
                if attempt > 0:
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
                else:
                    time.sleep(self.rate_limit_delay)
                
                headers = self._get_headers()
                
                response = requests.get(
                    self.base_url,
                    params=params,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # Rate limited
                    retry_after = int(response.headers.get('Retry-After', '60'))
                    logger.warning(f"CrossRef rate limited, waiting {retry_after} seconds")
                    
                    if attempt == max_retries - 1:
                        # Last attempt, raise the error
                        raise RateLimitError("CrossRef", retry_after)
                    
                    time.sleep(retry_after)
                    continue
                elif response.status_code == 401:
                    from ..utils.exceptions import AuthenticationError
                    raise AuthenticationError("CrossRef", "API authentication failed")
                elif response.status_code == 403:
                    from ..utils.exceptions import AuthenticationError
                    raise AuthenticationError("CrossRef", "Access forbidden - check API permissions")
                elif response.status_code >= 500:
                    if attempt == max_retries - 1:
                        raise APIUnavailableError("CrossRef", response.status_code, "Server error")
                    logger.warning(f"CrossRef server error {response.status_code}, retrying...")
                    continue
                else:
                    if attempt == max_retries - 1:
                        raise APIUnavailableError("CrossRef", response.status_code, response.text[:200])
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"CrossRef request error (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    # Let the decorator handle this
                    raise
        
        # Should not reach here due to exception handling above
        raise APIUnavailableError("CrossRef", message="Max retries exceeded")
    
    def _standardize_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Standardize papers to match expected schema"""
        standardized = []
        
        for paper in papers:
            try:
                # Handle title
                title_list = paper.get('title', [])
                title = title_list[0] if title_list else 'No title'
                
                # Handle authors
                authors_list = paper.get('author', [])
                author_names = []
                for author in authors_list:
                    given = author.get('given', '')
                    family = author.get('family', '')
                    if given and family:
                        author_names.append(f"{given} {family}")
                    elif family:
                        author_names.append(family)
                authors_str = ', '.join(author_names) if author_names else 'Unknown'
                
                # Handle publication date
                pub_date = paper.get('published-print') or paper.get('published-online')
                year = 'Unknown'
                if pub_date and 'date-parts' in pub_date:
                    try:
                        year_parts = pub_date['date-parts'][0]
                        if year_parts:
                            year = year_parts[0]
                    except (IndexError, TypeError):
                        pass
                
                # Handle DOI and URL
                doi = paper.get('DOI', '')
                url = f"https://doi.org/{doi}" if doi else paper.get('URL', '')
                
                # Handle citations (referenced-by-count)
                citation_count = paper.get('is-referenced-by-count', 0)
                # Ensure citation count is a proper integer or 'N/A'
                if citation_count is None or citation_count == 0:
                    citation_count = 0
                elif not isinstance(citation_count, int):
                    try:
                        citation_count = int(citation_count)
                    except (ValueError, TypeError):
                        citation_count = 0
                
                # Handle abstract (clean HTML if present)
                abstract = paper.get('abstract', '')
                if abstract:
                    # Remove HTML tags and clean up
                    import re
                    abstract = re.sub('<[^<]+?>', '', abstract)  # Remove HTML tags
                    abstract = abstract.replace('&nbsp;', ' ').replace('&amp;', '&')  # Clean entities
                    abstract = ' '.join(abstract.split())  # Normalize whitespace
                
                # Handle journal/venue
                container_title = paper.get('container-title', [])
                venue = container_title[0] if container_title else ''
                
                standardized_paper = {
                    'title': title,
                    'authors': authors_str,
                    'year': year,
                    'abstract': abstract,
                    'url': url,
                    'citations': citation_count,
                    'source': 'crossref',
                    'provider': self.get_provider_name(),
                    'venue': venue,
                    'doi': doi,
                    'publisher': paper.get('publisher', ''),
                    'type': paper.get('type', ''),
                    'created_date': paper.get('created', {}).get('date-time', ''),
                    'indexed_date': paper.get('indexed', {}).get('date-time', '')
                }
                
                standardized.append(standardized_paper)
                
            except Exception as e:
                continue
        
        return standardized
    
    def get_paper_by_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """Get a specific paper by DOI"""
        if not doi:
            return None
        
        try:
            url = f"https://api.crossref.org/works/{doi}"
            headers = self._get_headers()
            time.sleep(self.rate_limit_delay)
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                paper_data = data.get('message', {})
                if paper_data:
                    return self._standardize_papers([paper_data])[0]
            
        except Exception as e:
            pass
        
        return None

    def _filter_quality_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Additional quality filtering for papers"""
        quality_papers = []
        
        for paper in papers:
            # Skip papers with generic titles
            title = paper.get('title', '').lower()
            if self._is_generic_title(title):
                continue
            
            # Skip papers without proper authors (but be less strict)
            authors = paper.get('authors', '')
            if not authors or authors == 'Unknown':
                continue
            
            # Less restrictive citation filtering
            citations = paper.get('citations', 0)
            year = paper.get('year', 0)
            
            # Skip papers that clearly have no citation data AND are old
            if citations == 'N/A' and isinstance(year, int) and year < 2020:
                continue
            
            # More lenient venue filtering - just check it exists
            venue = paper.get('venue', '')
            # Commenting out venue requirement as it may be too restrictive
            # if not venue or len(venue.strip()) < 3:
            #     continue
            
            quality_papers.append(paper)
        
        return quality_papers
    
    def _is_generic_title(self, title: str) -> bool:
        """Check if title is too generic/vague"""
        generic_patterns = [
            'machine learning',
            'artificial intelligence', 
            'deep learning',
            'neural networks',
            'data mining',
            'introduction to',
            'overview of',
            'survey of',
            'review of'
        ]
        
        # If title is exactly one of these generic terms, it's too generic
        title_clean = title.strip().lower()
        if title_clean in generic_patterns:
            return True
        
        # If title is very short and contains only generic terms
        if len(title_clean.split()) <= 3:
            for pattern in generic_patterns:
                if pattern in title_clean and len(title_clean.replace(pattern, '').strip()) < 5:
                    return True
        
        return False
