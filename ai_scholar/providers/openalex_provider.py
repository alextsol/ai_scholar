from typing import List, Optional, Dict, Any
from ..interfaces.search_interface import ISearchProvider
from ..utils.exceptions import RateLimitError, APIUnavailableError, SearchError
from ..utils.error_handler import ErrorHandler, handle_provider_error
import requests
import time
import logging

logger = logging.getLogger(__name__)

class OpenAlexProvider(ISearchProvider):
    """OpenAlex search provider implementation"""
    
    def __init__(self, mailto: Optional[str] = None):
        self.mailto = mailto or "support@ai-scholar.com"
        self.base_url = "https://api.openalex.org/works"
        self.rate_limit_delay = 1.0  # Seconds between requests
        self.last_request_time = 0
    
    @handle_provider_error("OpenAlex")
    def search(self, query: str, limit: int, min_year: Optional[int] = None, max_year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search OpenAlex for papers"""
        if not self.validate_query(query):
            logger.warning(f"Invalid query provided to OpenAlex: '{query}'")
            return []  # Return empty list instead of raising error
        
        try:
            # Build search parameters - use proper OpenAlex search format
            # OpenAlex supports search in title, abstract, and fulltext
            query_clean = query.strip().replace('"', '')
            
            params = {
                "search": query_clean,  # Use the search parameter instead of filter
                "per-page": min(limit * 3, 200),  # Get more results to filter for relevance
                "sort": "relevance_score:desc"  # Sort by relevance first
            }
            
            # Add year filters if specified
            filters = []
            if min_year:
                filters.append(f"from_publication_date:{min_year}-01-01")
            if max_year:
                filters.append(f"to_publication_date:{max_year}-12-31")
            
            if filters:
                params["filter"] = ",".join(filters)
            
            # Make request with rate limiting
            response = self._make_request(params)
            
            if response and response.status_code == 200:
                data = response.json()
                papers = data.get('results', [])
                if not papers:
                    logger.info(f"OpenAlex returned no results for query: {query}")
                    return []
                
                standardized = self._standardize_papers(papers)
                
                # Apply improved quality filtering
                quality_papers = self._filter_quality_papers(standardized, query_clean)
                
                logger.info(f"OpenAlex found {len(quality_papers)} quality papers")
                return quality_papers[:limit]
            
            return []
            
        except Exception as e:
            logger.error(f"OpenAlex search error: {str(e)}")
            return []
    
    def get_provider_name(self) -> str:
        return "OpenAlex"
    
    def is_available(self) -> bool:
        """Check if OpenAlex API is available"""
        try:
            # Test with a simple query
            test_response = requests.get(
                self.base_url,
                params={
                    'filter': 'default.search:test',
                    'per-page': 1
                },
                timeout=10
            )
            return test_response.status_code == 200
        except:
            return False
    
    def validate_query(self, query: str) -> bool:
        """Validate OpenAlex query"""
        if not query or not query.strip():
            return False
        # OpenAlex requires at least 3 characters for meaningful search
        return len(query.strip()) >= 3
    
    def _make_request(self, params: Dict[str, Any]) -> Optional[requests.Response]:
        """Make request to OpenAlex API with rate limiting"""
        max_retries = 3
        base_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Rate limiting - ensure minimum time between requests
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
                    self.base_url,
                    params=params,
                    headers=headers,
                    timeout=30
                )
                
                self.last_request_time = time.time()
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # Rate limited
                    retry_after = response.headers.get('Retry-After')
                    if retry_after:
                        time.sleep(int(retry_after))
                    else:
                        time.sleep(base_delay * 2)
                    continue
                elif response.status_code == 500:
                    if attempt == max_retries - 1:
                        raise APIUnavailableError("OpenAlex", "Server error (HTTP 500)")
                    continue
                else:
                    if attempt == max_retries - 1:
                        raise APIUnavailableError("OpenAlex", f"HTTP {response.status_code}")
                    
            except requests.exceptions.Timeout:
                if attempt == max_retries - 1:
                    raise APIUnavailableError("OpenAlex", "Request timed out after 30 seconds")
            except requests.exceptions.ConnectionError:
                if attempt == max_retries - 1:
                    raise APIUnavailableError("OpenAlex", "Connection failed")
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise APIUnavailableError("OpenAlex", f"Request failed: {str(e)}")
        
        return None
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        return {
            'User-Agent': f'AI-Scholar/1.0 (mailto:{self.mailto})',
            'Accept': 'application/json'
        }
    
    def _standardize_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Standardize papers to match expected schema"""
        standardized = []
        
        for paper in papers:
            try:
                # Handle title
                title = paper.get('display_name', 'No title available')
                if not title or title.lower() == 'unknown':
                    continue
                
                # Handle authors
                authorships = paper.get('authorships', [])
                author_names = []
                for authorship in authorships:
                    author = authorship.get('author', {})
                    name = author.get('display_name', '')
                    if name:
                        author_names.append(name)
                
                # Keep as list for consistency with other providers
                authors = author_names if author_names else []
                
                # Handle year
                year = paper.get('publication_year')
                if not year:
                    # Try to extract from publication_date
                    pub_date = paper.get('publication_date', '')
                    if pub_date:
                        try:
                            year = int(pub_date.split('-')[0])
                        except:
                            year = 'Unknown'
                    else:
                        year = 'Unknown'
                
                # Handle abstract
                abstract = ''
                # OpenAlex doesn't provide abstracts directly in search results
                # but we can use the inverted abstract if available
                inverted_abstract = paper.get('abstract_inverted_index', {})
                if inverted_abstract:
                    # Reconstruct abstract from inverted index
                    words_with_positions = []
                    for word, positions in inverted_abstract.items():
                        for pos in positions:
                            words_with_positions.append((pos, word))
                    
                    # Sort by position and reconstruct
                    words_with_positions.sort(key=lambda x: x[0])
                    abstract = ' '.join([word for _, word in words_with_positions])
                    
                    # Truncate if too long
                    if len(abstract) > 1000:
                        abstract = abstract[:1000] + "..."
                
                # Handle citations
                citation_count = paper.get('cited_by_count', 0)
                
                # Handle DOI and URL
                doi = paper.get('doi', '')
                url = doi if doi else paper.get('id', '')  # OpenAlex ID as fallback
                
                # Handle venue
                venue = ''
                primary_location = paper.get('primary_location', {})
                if primary_location:
                    source = primary_location.get('source', {})
                    venue = source.get('display_name', '') if source else ''
                
                # Handle publication type
                publication_type = paper.get('type', 'journal-article')
                
                standardized_paper = {
                    'title': title,
                    'authors': authors,
                    'year': year,
                    'abstract': abstract,
                    'url': url,
                    'citations': citation_count,  # Use 'citations' to match Paper model
                    'source': 'openalex',
                    'provider': self.get_provider_name(),
                    'venue': venue,
                    'doi': doi,
                    'publication_type': publication_type,
                    'openalex_id': paper.get('id', ''),
                    'is_oa': paper.get('open_access', {}).get('is_oa', False),
                    'oa_url': paper.get('open_access', {}).get('oa_url', ''),
                    'published_date': paper.get('publication_date', '')
                }
                
                standardized.append(standardized_paper)
                
            except Exception as e:
                logger.warning(f"Error standardizing OpenAlex paper: {str(e)}")
                continue
        
        return standardized
    
    def _filter_quality_papers(self, papers: List[Dict[str, Any]], query: str = "") -> List[Dict[str, Any]]:
        """Filter papers for better quality with relevance scoring"""
        quality_papers = []
        query_words = query.lower().split() if query else []
        
        for paper in papers:
            # Skip papers without proper titles
            title = paper.get('title', '').strip()
            if not title or len(title) < 10:
                continue
                
            # Skip papers without authors
            authors = paper.get('authors', '')
            if not authors or authors == 'Unknown':
                continue
            
            # More lenient filtering - just need title, authors, and some identifier
            url = paper.get('url', '')
            doi = paper.get('doi', '')
            
            # Must have at least a URL or DOI
            if not url and not doi:
                continue
            
            # Calculate relevance score based on query matching
            relevance_score = 0
            title_lower = title.lower()
            abstract = paper.get('abstract', '').lower()
            
            # Score based on exact and partial query word matches
            for word in query_words:
                if len(word) > 2:  # Skip very short words
                    # Exact word matches in title are highly relevant
                    if f" {word} " in f" {title_lower} " or title_lower.startswith(word) or title_lower.endswith(word):
                        relevance_score += 5
                    # Partial matches in title
                    elif word in title_lower:
                        relevance_score += 3
                    
                    # Exact word matches in abstract
                    if f" {word} " in f" {abstract} " and abstract:
                        relevance_score += 2
                    # Partial matches in abstract
                    elif word in abstract and abstract:
                        relevance_score += 1
            
            # Boost if all query words appear somewhere
            if len(query_words) > 1:
                words_found = sum(1 for word in query_words if len(word) > 2 and (word in title_lower or word in abstract))
                if words_found == len([w for w in query_words if len(w) > 2]):
                    relevance_score += 3
            
            # Require minimum relevance for short queries
            if len(query_words) == 1 and len(query_words[0]) <= 4:
                # For short single-word queries, require high relevance
                if relevance_score < 3:
                    continue
            elif len(query_words) <= 2:
                # For 1-2 word queries, require some relevance
                if relevance_score < 2:
                    continue
            
            # Quality score for sorting
            quality_score = relevance_score  # Start with relevance
            
            # Boost for having DOI
            if doi:
                quality_score += 2
            
            # Boost for having abstract
            if paper.get('abstract', '').strip() and len(paper.get('abstract', '')) > 30:
                quality_score += 2
            
            # Bonus for citation count
            citations = paper.get('citations', 0)
            if isinstance(citations, int) and citations > 0:
                if citations >= 100:
                    quality_score += 3
                elif citations >= 50:
                    quality_score += 2
                elif citations >= 10:
                    quality_score += 1
            
            # Bonus for recent papers (within last 10 years)
            year = paper.get('year')
            if isinstance(year, int) and year >= 2014:
                quality_score += 1
            
            # Bonus for open access
            if paper.get('is_oa', False):
                quality_score += 1
                
            paper['_quality_score'] = quality_score
            quality_papers.append(paper)
        
        # Sort by quality score and return top results
        quality_papers.sort(key=lambda p: p.get('_quality_score', 0), reverse=True)
        
        # Remove the quality score field
        for paper in quality_papers:
            paper.pop('_quality_score', None)
            
        return quality_papers
    
    def get_paper_details(self, openalex_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific paper by OpenAlex ID"""
        if not openalex_id:
            return None
        
        try:
            # Ensure the ID is in proper format
            if not openalex_id.startswith('https://openalex.org/'):
                openalex_id = f"https://openalex.org/{openalex_id}"
            
            params = {
                'mailto': self.mailto
            }
            
            headers = self._get_headers()
            time.sleep(self.rate_limit_delay)
            
            response = requests.get(openalex_id, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                paper_data = response.json()
                return self._standardize_papers([paper_data])[0]
            
        except Exception as e:
            logger.error(f"Error fetching OpenAlex paper details: {str(e)}")
        
        return None
