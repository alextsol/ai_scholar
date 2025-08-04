from typing import List, Optional, Dict, Any
from ..interfaces.search_interface import ISearchProvider
import requests
import time
import random

class ArxivSearchProvider(ISearchProvider):
    """arXiv search provider implementation"""
    
    def __init__(self):
        self.base_url = "http://export.arxiv.org/api/query"
        self.max_results_per_request = 100
    
    def search(self, query: str, limit: int, min_year: Optional[int] = None, max_year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search arXiv for papers"""
        if not self.validate_query(query):
            return []
        
        try:
            # Build search parameters
            search_query = self._build_arxiv_query(query, min_year, max_year)
            
            params = {
                'search_query': search_query,
                'start': 0,
                'max_results': min(limit, self.max_results_per_request),
                'sortBy': 'relevance',
                'sortOrder': 'descending'
            }
            
            # Make request with retry logic
            response = self._make_request(params)
            
            if response and response.status_code == 200:
                papers = self._parse_arxiv_response(response.text)
                return self._standardize_papers(papers)
            
            return []
            
        except Exception as e:
            return []
    
    def get_provider_name(self) -> str:
        return "arXiv"
    
    def is_available(self) -> bool:
        """Check if arXiv API is available"""
        try:
            test_response = requests.get(self.base_url, timeout=10)
            return test_response.status_code == 200
        except:
            return False
    
    def validate_query(self, query: str) -> bool:
        """Validate arXiv query"""
        if not query or not query.strip():
            return False
        # arXiv has a minimum query length
        return len(query.strip()) >= 3
    
    def _build_arxiv_query(self, query: str, min_year: Optional[int], max_year: Optional[int]) -> str:
        """Build arXiv-specific query string"""
        # Clean the query
        clean_query = query.strip()
        
        # For machine learning, use a simpler approach
        # Search in all fields (title, abstract, comments, etc.)
        arxiv_query = f"all:\"{clean_query}\""
        
        # Add date filters if specified - use simpler format
        if min_year or max_year:
            if min_year and max_year:
                arxiv_query += f" AND submittedDate:[{min_year}0101 TO {max_year}1231]"
            elif min_year:
                arxiv_query += f" AND submittedDate:[{min_year}0101 TO *]"
            elif max_year:
                arxiv_query += f" AND submittedDate:[* TO {max_year}1231]"
        
        return arxiv_query
    
    def _make_request(self, params: Dict[str, Any]) -> Optional[requests.Response]:
        """Make request to arXiv API with retry logic"""
        max_retries = 3
        delay = 1
        
        for attempt in range(max_retries):
            try:
                # Add delay to respect rate limits
                if attempt > 0:
                    time.sleep(delay * attempt)
                
                response = requests.get(
                    self.base_url,
                    params=params,
                    timeout=30,
                    headers={'User-Agent': 'AI-Scholar/1.0'}
                )
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # Rate limited
                    time.sleep(delay * 2)
                    continue
                else:
                    return None
                    
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    return None
        
        return None
    
    def _parse_arxiv_response(self, xml_content: str) -> List[Dict[str, Any]]:
        """Parse arXiv XML response"""
        import xml.etree.ElementTree as ET
        
        papers = []
        
        try:
            root = ET.fromstring(xml_content)
            
            # Define namespaces
            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            entries = root.findall('atom:entry', namespaces)
            
            for entry in entries:
                paper = {}
                
                # Title
                title_elem = entry.find('atom:title', namespaces)
                if title_elem is not None:
                    paper['title'] = title_elem.text.strip().replace('\n', ' ')
                
                # Authors
                authors = []
                author_elems = entry.findall('atom:author', namespaces)
                for author in author_elems:
                    name_elem = author.find('atom:name', namespaces)
                    if name_elem is not None:
                        authors.append(name_elem.text.strip())
                paper['authors'] = ', '.join(authors) if authors else 'Unknown'
                
                # Abstract
                summary_elem = entry.find('atom:summary', namespaces)
                if summary_elem is not None:
                    paper['abstract'] = summary_elem.text.strip().replace('\n', ' ')
                
                # Published date
                published_elem = entry.find('atom:published', namespaces)
                if published_elem is not None:
                    pub_date = published_elem.text.strip()
                    # Extract year from date (format: 2023-01-15T18:30:00Z)
                    try:
                        paper['year'] = int(pub_date.split('-')[0])
                    except:
                        paper['year'] = 'Unknown'
                
                # arXiv ID and URL
                id_elem = entry.find('atom:id', namespaces)
                if id_elem is not None:
                    arxiv_url = id_elem.text.strip()
                    paper['url'] = arxiv_url
                    # Extract arXiv ID
                    if 'arxiv.org/abs/' in arxiv_url:
                        paper['arxiv_id'] = arxiv_url.split('/')[-1]
                
                # Categories
                categories = []
                category_elems = entry.findall('atom:category', namespaces)
                for cat in category_elems:
                    term = cat.get('term')
                    if term:
                        categories.append(term)
                paper['categories'] = categories
                
                # No citation count available from arXiv directly
                paper['citations'] = 'N/A'
                
                if paper.get('title'):  # Only add if we have at least a title
                    papers.append(paper)
                    
        except ET.ParseError as e:
            pass
        except Exception as e:
            pass
        
        return papers
    
    def _standardize_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Standardize paper format to match expected schema"""
        standardized = []
        
        for paper in papers:
            standardized_paper = {
                'title': paper.get('title', 'No title'),
                'authors': paper.get('authors', 'Unknown'),
                'year': paper.get('year', 'Unknown'),
                'abstract': paper.get('abstract', ''),
                'url': paper.get('url', ''),
                'citations': paper.get('citations', 'N/A'),
                'source': 'arxiv',
                'provider': self.get_provider_name(),
                'categories': paper.get('categories', []),
                'arxiv_id': paper.get('arxiv_id', '')
            }
            standardized.append(standardized_paper)
        
        return standardized
