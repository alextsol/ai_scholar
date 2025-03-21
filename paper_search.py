# paper_search.py

from searches.semantic_search import search as semantic_search
from searches.arxiv_search import search as arxiv_search
from searches.crossref_search import search as crossref_search
from searches.core_search import search as core_search
from config import DEFAULT_SEARCH_BACKEND

def format_items(items, mapping):
    return [{ key: func(item) for key, func in mapping.items() } for item in items]

def generic_requests_search(url, params, mapping, headers=None, extractor=None):
    import requests
    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        return f"Error: Unable to fetch papers (Status Code: {response.status_code})"
    data = extractor(response) if extractor else response.json()
    return format_items(data, mapping)

BACKENDS = {
    "semantic_scholar": semantic_search,
    "arxiv": arxiv_search,
    "crossref": crossref_search,
    "core": core_search,
}

def search_papers(query, limit=10, backend=None):
    if backend is None:
        backend = DEFAULT_SEARCH_BACKEND
    if backend not in BACKENDS:
        return f"Error: Unknown backend '{backend}' specified."
    return BACKENDS[backend](query, limit)
