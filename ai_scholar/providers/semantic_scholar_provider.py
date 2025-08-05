from typing import List, Optional, Dict, Any
from ..interfaces.search_interface import ISearchProvider
import requests
import time
import json

class SemanticScholarProvider(ISearchProvider):
    """Semantic Scholar search provider implementation"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        self.search_url = f"{self.base_url}/paper/search"
        self.rate_limit_delay = 1.0  # Seconds between requests
    
    def search(self, query: str, limit: int, min_year: Optional[int] = None, max_year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search Semantic Scholar for papers"""
        if not self.validate_query(query):
            return []
        
        try:
            # Build search parameters
            params = {
                'query': query.strip(),
                'limit': min(limit, 100),  # API limit
                'fields': 'paperId,title,authors,year,abstract,citationCount,url,venue,publicationDate'
            }
            
            # Add year filters if specified
            if min_year:
                params['year'] = f"{min_year}-"
            if max_year:
                if min_year:
                    params['year'] = f"{min_year}-{max_year}"
                else:
                    params['year'] = f"-{max_year}"
            
            # Make request with rate limiting
            response = self._make_request(params)
            
            if response and response.status_code == 200:
                data = response.json()
                papers = data.get('data', [])
                return self._standardize_papers(papers)
            
            return []
            
        except Exception as e:
            return []
    
    def get_provider_name(self) -> str:
        return "Semantic Scholar"
    
    def is_available(self) -> bool:
        """Check if Semantic Scholar API is available"""
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
        """Validate Semantic Scholar query"""
        if not query or not query.strip():
            return False
        return len(query.strip()) >= 3
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with API key if available"""
        headers = {
            'User-Agent': 'AI-Scholar/1.0 (mailto:support@ai-scholar.com)',
            'Content-Type': 'application/json'
        }
        
        if self.api_key:
            headers['x-api-key'] = self.api_key
        
        return headers
    
    def _make_request(self, params: Dict[str, Any]) -> Optional[requests.Response]:
        """Make request to Semantic Scholar API with rate limiting"""
        max_retries = 3
        base_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Rate limiting delay
                if attempt > 0:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
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
                    retry_after = response.headers.get('Retry-After')
                    if retry_after:
                        time.sleep(int(retry_after))
                    else:
                        time.sleep(base_delay * 2)
                    continue
                elif response.status_code == 403:
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
                authors_list = paper.get('authors', [])
                if isinstance(authors_list, list):
                    author_names = []
                    for author in authors_list:
                        if isinstance(author, dict):
                            name = author.get('name', '')
                        else:
                            name = str(author)
                        if name:
                            author_names.append(name)
                    authors_str = ', '.join(author_names) if author_names else 'Unknown'
                else:
                    authors_str = str(authors_list) if authors_list else 'Unknown'
                
                # Handle year
                year = paper.get('year')
                if not year:
                    # Try to extract from publicationDate
                    pub_date = paper.get('publicationDate', '')
                    if pub_date and isinstance(pub_date, str):
                        try:
                            year = int(pub_date.split('-')[0])
                        except:
                            year = 'Unknown'
                    else:
                        year = 'Unknown'
                
                # Handle citations
                citation_count = paper.get('citationCount')
                if citation_count is None:
                    citation_count = 'N/A'
                
                # Build URL
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
                    'source': 'semantic_scholar',
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
        """Get detailed information about a specific paper"""
        if not paper_id:
            return None
        
        try:
            url = f"{self.base_url}/paper/{paper_id}"
            params = {
                'fields': 'paperId,title,authors,year,abstract,citationCount,url,venue,publicationDate,references,citations'
            }
            
            headers = self._get_headers()
            time.sleep(self.rate_limit_delay)
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                paper_data = response.json()
                return self._standardize_papers([paper_data])[0]
            
        except Exception as e:
            pass
        
        return None
