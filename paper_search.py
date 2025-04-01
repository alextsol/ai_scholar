# paper_search.py
from venv import logger
from searches.semantic_search import search as semantic_conf
from searches.arxiv_search import search as arxiv_conf
from searches.crossref_search import search as crossref_conf
from searches.core_search import search as core_conf
from config import DEFAULT_SEARCH_BACKEND
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from utils import format_items, generic_requests_search

BACKENDS = {
    "semantic_scholar": semantic_conf,
    "arxiv": arxiv_conf,
    "crossref": crossref_conf,
    "core": core_conf,
}

@retry(
    stop=stop_after_attempt(10),  
    wait=wait_fixed(5),           
    retry=retry_if_exception_type(Exception)  
)
def search_papers(query, limit=10, backend=None):
    if backend is None:
        backend = DEFAULT_SEARCH_BACKEND
    if backend not in BACKENDS:
        return f"Error: Unknown backend '{backend}' specified."
    
    conf = BACKENDS[backend](query, limit)
    logger.debug(conf);
    if backend == "arxiv":
        return format_items(conf["results"], conf["mapping"])
        
    return generic_requests_search(conf["url"], conf["params"], mapping = conf["mapping"], extractor = conf.get("extractor") )
