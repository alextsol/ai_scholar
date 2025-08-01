from typing import List, Optional, Dict, Any
from ..interfaces.search_interface import ISearchProvider
import requests
import time

class COREProvider(ISearchProvider):
    """CORE (COnnecting REpositories) search provider implementation"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://api.core.ac.uk/v3"
        self.search_url = f"{self.base_url}/search/works"
        self.rate_limit_delay = 1.0
    
    def search(self, query: str, limit: int, min_year: Optional[int] = None, max_year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search CORE for papers"""
        if not self.validate_query(query):
            return []
        
        try:
            # Build search parameters
            params = {
                'q': query.strip(),
                'limit': min(limit, 100),  # CORE API limit
                'offset': 0,
                'sort': 'relevance'
            }
            
            # Add year filters if specified
            if min_year or max_year:
                year_filter = self._build_year_filter(min_year, max_year)
                if year_filter:
                    params['q'] = f"{params['q']} AND {year_filter}"
            
            # Make request
            response = self._make_request(params)
            
            if response and response.status_code == 200:
                data = response.json()
                papers = data.get('results', [])
                return self._standardize_papers(papers)
            
            return []
            
        except Exception as e:
            print(f"CORE search error: {e}")
            return []
    
    def get_provider_name(self) -> str:
        return "CORE"
    
    def is_available(self) -> bool:
        """Check if CORE API is available"""
        try:
            headers = self._get_headers()
            test_response = requests.get(
                self.search_url,
                params={'q': 'test', 'limit': 1},
                headers=headers,
                timeout=10
            )
            return test_response.status_code in [200, 401]  # 401 means API key required but service available
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
    
    def _make_request(self, params: Dict[str, Any]) -> Optional[requests.Response]:
        """Make request to CORE API with rate limiting"""
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
                    self.search_url,
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
                elif response.status_code == 401:
                    print("CORE API requires authentication - please provide API key")
                    return None
                elif response.status_code == 403:
                    print("CORE API access forbidden - check API key")
                    return None
                else:
                    if attempt == max_retries - 1:
                        print(f"CORE API returned status code: {response.status_code}")
                        return None
                    
            except requests.exceptions.RequestException as e:
                print(f"CORE request attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    return None
        
        return None
    
    def _standardize_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
                citation_count = paper.get('citationCount', 'N/A')
                
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
                print(f"Error standardizing CORE paper: {e}")
                continue
        
        return standardized
    
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
                    return self._standardize_papers([paper_data])[0]
            
        except Exception as e:
            print(f"Error getting paper by CORE ID: {e}")
        
        return None
