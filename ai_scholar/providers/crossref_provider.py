from typing import List, Optional, Dict, Any
from ..interfaces.search_interface import ISearchProvider
from ..utils.exceptions import RateLimitError, APIUnavailableError, SearchError
from ..utils.error_handler import handle_provider_error
import requests
import time
import logging

logger = logging.getLogger(__name__)

class CrossRefProvider(ISearchProvider):    
    def __init__(self, api_key: Optional[str] = None, mailto: Optional[str] = None):
        self.api_key = api_key
        self.mailto = mailto or "support@ai-scholar.com"
        self.base_url = "https://api.crossref.org/works"
        self.rate_limit_delay = 1.0  
    
    @handle_provider_error("CrossRef")
    def search(self, query: str, limit: int, min_year: Optional[int] = None, max_year: Optional[int] = None) -> List[Dict[str, Any]]:
        if not self.validate_query(query):
            raise SearchError(f"Invalid query: {query}", "Please enter a valid search query with at least 3 characters.")

        params = {
            'query': query.strip(),
            'rows': min(limit * 2, 500),  
            'sort': 'is-referenced-by-count', 
            'order': 'desc'
        }
        
        filters = []
        
        filters.append('type:journal-article')
        
        if min_year:
            filters.append(f"from-pub-date:{min_year}")
        if max_year:
            filters.append(f"until-pub-date:{max_year}")
        else:
            from datetime import datetime
            current_year = datetime.now().year
            filters.append(f"from-pub-date:{current_year - 20}")
        
        params['filter'] = ','.join(filters)

        response = self._make_request(params)
        
        if response and response.status_code == 200:
            data = response.json()
            papers = data.get('message', {}).get('items', [])
            standardized = self._standardize_papers(papers)
            
            quality_papers = self._filter_quality_papers(standardized)
            
            return quality_papers[:limit]
        
        raise APIUnavailableError("CrossRef", message="No response received from CrossRef API")
    
    def get_provider_name(self) -> str:
        return "CrossRef"
    
    def is_available(self) -> bool:
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
        if not query or not query.strip():
            return False
        return len(query.strip()) >= 2
    
    def _get_headers(self) -> Dict[str, str]:
        headers = {
            'User-Agent': f'AI-Scholar/1.0 (mailto:{self.mailto})',
            'Accept': 'application/json'
        }
        
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        return headers
    
    def _make_request(self, params: Dict[str, Any]) -> Optional[requests.Response]:
        max_retries = 3
        base_delay = 2
        
        for attempt in range(max_retries):
            try:
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
                    raise
        
        raise APIUnavailableError("CrossRef", message="Max retries exceeded")
    
    def _standardize_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        standardized = []
        
        for paper in papers:
            try:
                title_list = paper.get('title', [])
                title = title_list[0] if title_list else 'No title'
                
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
                
                pub_date = paper.get('published-print') or paper.get('published-online')
                year = 'Unknown'
                if pub_date and 'date-parts' in pub_date:
                    try:
                        year_parts = pub_date['date-parts'][0]
                        if year_parts:
                            year = year_parts[0]
                    except (IndexError, TypeError):
                        pass
                
                doi = paper.get('DOI', '')
                url = f"https://doi.org/{doi}" if doi else paper.get('URL', '')
                
                citation_count = paper.get('is-referenced-by-count', 0)
                if citation_count is None or citation_count == 0:
                    citation_count = 0
                elif not isinstance(citation_count, int):
                    try:
                        citation_count = int(citation_count)
                    except (ValueError, TypeError):
                        citation_count = 0
                
                abstract = paper.get('abstract', '')
                if abstract:
                    # Remove HTML tags and clean up
                    import re
                    abstract = re.sub('<[^<]+?>', '', abstract) 
                    abstract = abstract.replace('&nbsp;', ' ').replace('&amp;', '&') 
                    abstract = ' '.join(abstract.split()) 
                
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

    def _filter_quality_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        quality_papers = []
        
        for paper in papers:
            title = paper.get('title', '').lower()
            if self._is_generic_title(title):
                continue
            
            authors = paper.get('authors', '')
            if not authors or authors == 'Unknown':
                continue
            
            citations = paper.get('citations', 0)
            year = paper.get('year', 0)
            
            # Skip very old papers with no citations
            if citations == 'N/A' and isinstance(year, int) and year < 2020:
                continue
            
            # Venue check - now correctly accessing the venue field
            venue = paper.get('venue', '')
            # Commenting out venue requirement as it may be too restrictive
            # if not venue or len(venue.strip()) < 3:
            #     continue
            
            quality_papers.append(paper)
        
        return quality_papers
    
    def _is_generic_title(self, title: str) -> bool:
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
        
        title_clean = title.strip().lower()
        if title_clean in generic_patterns:
            return True
        
        if len(title_clean.split()) <= 3:
            for pattern in generic_patterns:
                if pattern in title_clean and len(title_clean.replace(pattern, '').strip()) < 5:
                    return True
        
        return False
