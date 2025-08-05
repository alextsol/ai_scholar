from typing import List, Optional, Dict, Any
from ..interfaces.search_interface import ISearchProvider
from ..enums.providers import ProviderType
import requests
import time

class SemanticScholarProvider(ISearchProvider):
    API_LIMIT = 100
    MIN_QUERY_LENGTH = 3
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3
    BASE_DELAY = 2
    DEFAULT_FIELDS = 'paperId,title,authors,year,abstract,citationCount,url,venue,publicationDate'
    DETAIL_FIELDS = 'paperId,title,authors,year,abstract,citationCount,url,venue,publicationDate,references,citations'
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        self.search_url = f"{self.base_url}/paper/search"
        self.rate_limit_delay = 1.0
    
    def search(self, query: str, limit: int, min_year: Optional[int] = None, max_year: Optional[int] = None) -> List[Dict[str, Any]]:
        if not self.validate_query(query):
            return []
        
        try:
            params = {
                'query': query.strip(),
                'limit': min(limit, self.API_LIMIT),
                'fields': self.DEFAULT_FIELDS
            }
            
            if min_year:
                params['year'] = f"{min_year}-"
            if max_year:
                if min_year:
                    params['year'] = f"{min_year}-{max_year}"
                else:
                    params['year'] = f"-{max_year}"
            
            response = self._make_request(params)
            
            if response and response.status_code == 200:
                data = response.json()
                papers = data.get('data', [])
                return self._standardize_papers(papers)
            
            return []
            
        except Exception as e:
            return []
    
    def get_provider_name(self) -> str:
        return ProviderType.SEMANTIC_SCHOLAR.value
    
    def is_available(self) -> bool:
        try:
            test_url = f"{self.base_url}/paper/search"
            headers = self._get_headers()
            
            test_response = requests.get(
                test_url,
                params={'query': 'test', 'limit': 1},
                headers=headers,
                timeout=10
            )
            
            return test_response.status_code in [200, 429]
        except:
            return False
    
    def validate_query(self, query: str) -> bool:
        if not query or not query.strip():
            return False
        return len(query.strip()) >= self.MIN_QUERY_LENGTH
    
    def _get_headers(self) -> Dict[str, str]:
        headers = {
            'User-Agent': 'AI-Scholar/1.0 (mailto:support@ai-scholar.com)',
            'Content-Type': 'application/json'
        }
        
        if self.api_key:
            headers['x-api-key'] = self.api_key
        
        return headers
    
    def _make_request(self, params: Dict[str, Any]) -> Optional[requests.Response]:
        for attempt in range(self.MAX_RETRIES):
            try:
                if attempt > 0:
                    delay = self.BASE_DELAY * (2 ** attempt)
                    time.sleep(delay)
                else:
                    time.sleep(self.rate_limit_delay)
                
                headers = self._get_headers()
                
                response = requests.get(
                    self.search_url,
                    params=params,
                    headers=headers,
                    timeout=self.REQUEST_TIMEOUT
                )
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:
                    retry_after = response.headers.get('Retry-After')
                    if retry_after:
                        time.sleep(int(retry_after))
                    else:
                        time.sleep(self.BASE_DELAY * 2)
                    continue
                elif response.status_code == 403:
                    return None
                else:
                    if attempt == self.MAX_RETRIES - 1:
                        return None
                    
            except requests.exceptions.RequestException:
                if attempt == self.MAX_RETRIES - 1:
                    return None
        
        return None
    
    def _extract_authors(self, authors_list: Any) -> str:
        if isinstance(authors_list, list):
            author_names = []
            for author in authors_list:
                if isinstance(author, dict):
                    name = author.get('name', '')
                else:
                    name = str(author)
                if name:
                    author_names.append(name)
            return ', '.join(author_names) if author_names else 'Unknown'
        return str(authors_list) if authors_list else 'Unknown'
    
    def _extract_year(self, paper: Dict[str, Any]) -> Any:
        year = paper.get('year')
        if not year:
            pub_date = paper.get('publicationDate', '')
            if pub_date and isinstance(pub_date, str):
                try:
                    year = int(pub_date.split('-')[0])
                except:
                    year = 'Unknown'
            else:
                year = 'Unknown'
        return year

    def _standardize_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        standardized = []
        
        for paper in papers:
            try:
                authors_str = self._extract_authors(paper.get('authors', []))
                year = self._extract_year(paper)
                
                citation_count = paper.get('citationCount')
                if citation_count is None:
                    citation_count = 'N/A'
                
                paper_id = paper.get('paperId', '')
                url = paper.get('url', '')
                if not url and paper_id:
                    url = f"https://www.semanticscholar.org/paper/{paper_id}"
                
                standardized_paper = {
                    'title': paper.get('title', 'No title'),
                    'authors': authors_str,
                    'year': year,
                    'abstract': paper.get('abstract', ''),
                    'url': url,
                    'citations': citation_count,
                    'source': ProviderType.SEMANTIC_SCHOLAR.value,
                    'provider': self.get_provider_name(),
                    'venue': paper.get('venue', ''),
                    'paper_id': paper_id,
                    'publication_date': paper.get('publicationDate', '')
                }
                
                standardized.append(standardized_paper)
                
            except Exception as e:
                continue
        
        return standardized
    
    def get_paper_details(self, paper_id: str) -> Optional[Dict[str, Any]]:
        if not paper_id:
            return None
        
        try:
            url = f"{self.base_url}/paper/{paper_id}"
            params = {
                'fields': self.DETAIL_FIELDS
            }
            
            headers = self._get_headers()
            time.sleep(self.rate_limit_delay)
            
            response = requests.get(url, params=params, headers=headers, timeout=self.REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                paper_data = response.json()
                return self._standardize_papers([paper_data])[0]
            
        except Exception:
            pass
        
        return None
