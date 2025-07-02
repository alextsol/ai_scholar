from searches.semantic_search import search as semantic_search
from searches.arxiv_search import search as arxiv_search
from searches.crossref_search import search as crossref_search
from searches.core_search import search as core_search
from config import DEFAULT_SEARCH_BACKEND
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from utils import filter_results_by_year

BACKENDS = {
    #"semantic_scholar": semantic_search,
    "arxiv": arxiv_search,
    #"crossref": crossref_search,
    #"core": core_search,
}

@retry(
    stop=stop_after_attempt(10),  
    wait=wait_fixed(5),           
    retry=retry_if_exception_type(Exception)  
)
def search_papers(query, limit, backend=None, min_year=None, max_year=None):
    if backend is None:
        backend = DEFAULT_SEARCH_BACKEND
    if backend not in BACKENDS:
        return f"Error: Unknown backend '{backend}' specified."
    
    try:
        response = BACKENDS[backend](query, limit, min_year, max_year)
    except TypeError:
        response = BACKENDS[backend](query, limit)
    
    if isinstance(response, list) and response:
        if backend == "arxiv" and (min_year or max_year):
            response = filter_results_by_year(response, min_year, max_year)
        return response
    return response
