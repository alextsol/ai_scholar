from typing import List, Optional, Dict, Any
from ..interfaces.search_interface import ISearchProvider
import requests
import time

class CrossRefProvider(ISearchProvider):
    """CrossRef search provider implementation"""
    
    def __init__(self, api_key: Optional[str] = None, mailto: Optional[str] = None):
        self.api_key = api_key
        self.mailto = mailto or "support@ai-scholar.com"
        self.base_url = "https://api.crossref.org/works"
        self.rate_limit_delay = 1.0  # Polite rate limiting
    
    def search(self, query: str, limit: int, min_year: Optional[int] = None, max_year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search CrossRef for papers"""
        if not self.validate_query(query):
            return []
        
        try:
            # Build search parameters
            params = {
                'query': query.strip(),
                'rows': min(limit, 1000),  # CrossRef allows up to 1000
                'sort': 'relevance',
                'order': 'desc'
            }
            
            # Add year filters if specified
            if min_year or max_year:
                filters = []
                if min_year:
                    filters.append(f"from-pub-date:{min_year}")
                if max_year:
                    filters.append(f"until-pub-date:{max_year}")
                params['filter'] = ','.join(filters)
            
            # Make request with rate limiting
            response = self._make_request(params)
            
            if response and response.status_code == 200:
                data = response.json()
                papers = data.get('message', {}).get('items', [])
                return self._standardize_papers(papers)
            
            return []
            
        except Exception as e:
            return []
    
    def get_provider_name(self) -> str:
        return "CrossRef"
    
    def is_available(self) -> bool:
        """Check if CrossRef API is available"""
        try:
            # Test with a simple query
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
        """Make request to CrossRef API with rate limiting"""
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
                    retry_after = response.headers.get('Retry-After', '5')
                    time.sleep(int(retry_after))
                    continue
                elif response.status_code in [403, 404]:
                    return None
                else:
                    if attempt == max_retries - 1:
                        return None
                    
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    return None
        
        return None
    
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
                citation_count = paper.get('is-referenced-by-count', 'N/A')
                
                # Handle abstract (not usually available in CrossRef)
                abstract = paper.get('abstract', '')
                
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
