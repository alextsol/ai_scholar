from searches.semantic_search import search as semantic_search
from searches.arxiv_search import search as arxiv_search
from searches.crossref_search import search as crossref_search
from searches.core_search import search as core_search
from .config import DEFAULT_SEARCH_BACKEND
from .cache import get_cache_key, get_cached_result, cache_result, cleanup_expired_cache
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests
import time
import random

from utils.utils import filter_results_by_year

BACKENDS = {
    "semantic_scholar": semantic_search,
    "arxiv": arxiv_search,
    "crossref": crossref_search,
    #"core": core_search,
}

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=5, max=120),
    retry=retry_if_exception_type((requests.exceptions.RequestException,)),
    reraise=True
)
def search_papers(query, limit, backend=None, min_year=None, max_year=None):
    cleanup_expired_cache()
    
    if backend is None:
        backend = DEFAULT_SEARCH_BACKEND
    if backend not in BACKENDS:
        return f"Error: Unknown backend '{backend}' specified."
    
    cache_key = get_cache_key(query, limit, backend, min_year, max_year)
    cached_result = get_cached_result(cache_key)
    if cached_result is not None:
        return cached_result
    
    if backend == "semantic_scholar":
        time.sleep(random.uniform(2, 5))
    
    try:
        response = BACKENDS[backend](query, limit, min_year, max_year)
        
        if isinstance(response, str) and response.startswith("Error:"):
            return response
            
    except TypeError:
        try:
            response = BACKENDS[backend](query, limit)
        except Exception as e:
            return f"Error: Failed to search {backend} - {str(e)}"
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            return f"Error: Rate limit exceeded for {backend}. Please try again in a few minutes."
        else:
            return f"Error: HTTP {e.response.status_code} from {backend}"
    except Exception as e:
        return f"Error: Failed to search {backend} - {str(e)}"
    
    if isinstance(response, list) and response:
        if backend == "arxiv" and (min_year or max_year):
            response = filter_results_by_year(response, min_year, max_year)
        
        cache_result(cache_key, response)
        return response
    elif isinstance(response, str):
        return response
    else:
        cache_result(cache_key, response)
        return response
