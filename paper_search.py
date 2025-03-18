import requests
import arxiv
from scholarly import scholarly
from collections import Counter
from config import (
    SEMANTIC_SCHOLAR_API_URL,
    CROSSREF_API_URL,
    CORE_API_URL,
    CORE_API_KEY,
)

def format_items(items, mapping):
    return [{ key: func(item) for key, func in mapping.items() } for item in items]

def generic_requests_search(url, params, mapping, headers=None, extractor=None):
    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        return f"Error: Unable to fetch papers (Status Code: {response.status_code})"
    data = extractor(response) if extractor else response.json()
    return format_items(data, mapping)

def semantic_scholar_search(query, limit=10):
    params = {
        "query": query,
        "limit": limit,
        "fields": "title,abstract,authors,year,url"
    }
    response = requests.get(SEMANTIC_SCHOLAR_API_URL, params=params)
    if response.status_code != 200:
        return f"Error: Unable to fetch papers (Status Code: {response.status_code})"
    
    json_response = response.json()
    data = json_response.get('data', [])
    
    # Ensure data is a list and filter out non-dictionary items.
    if not isinstance(data, list):
        return f"Unexpected data format: {json_response}"
    
    data = [item for item in data if isinstance(item, dict)]
    
    if not data:
        return []
    
    mapping = {
        'title': lambda item: item.get('title', 'No title'),
        'abstract': lambda item: item.get('abstract', 'No abstract available'),
        'authors': lambda item: ', '.join(
            [author.get('name', 'Unknown') for author in item.get('authors', []) if isinstance(author, dict)]
        ),
        'year': lambda item: item.get('year', 'Unknown year'),
        'url': lambda item: item.get('url', 'No URL available'),
        'source': lambda item: "semantic_scholar"
    }
    
    return format_items(data, mapping)

def crossref_search(query, limit=10):
    params = {"query": query, "rows": limit}
    mapping = {
        'title': lambda item: item.get('title', ['No title'])[0],
        'abstract': lambda item: item.get('abstract', 'No abstract available'),
        'authors': lambda item: ', '.join([f"{author.get('given', '')} {author.get('family', '')}".strip() 
                                            for author in item.get('author', [])]),
        'year': lambda item: item.get('issued', {}).get('date-parts', [[None]])[0][0],
        'url': lambda item: item.get('URL', 'No URL available'),
        'source': lambda item: "crossref"
    }
    extractor = lambda r: r.json()['message']['items']
    return generic_requests_search(CROSSREF_API_URL, params, mapping, extractor=extractor)

def core_search(query, limit=10):
    params = {"q": query, "limit": limit}
    headers = {"Authorization": f"Bearer {CORE_API_KEY}"}
    mapping = {
        'title': lambda item: item.get('title', 'No title'),
        'abstract': lambda item: item.get('abstract', 'No abstract available'),
         'authors': lambda item: ', '.join([
            author.get('name', 'Unknown') if isinstance(author, dict) else str(author)
            for author in item.get('authors', [])
        ]),
        'year': lambda item: item.get('yearPublished', 'Unknown year'),
        'url': lambda item: item.get('downloadUrl', 'No URL available'),
        'source': lambda item: "core"
    }
    extractor = lambda r: r.json().get('results', [])
    return generic_requests_search(CORE_API_URL, params, mapping, headers=headers, extractor=extractor)

def arxiv_search(query, limit=10):
    search = arxiv.Search(query=query, max_results=limit, sort_by=arxiv.SortCriterion.Relevance)
    results = list(search.results())
    
    valid_results = []
    for r in results:
        try:
            _ = r.title
            valid_results.append(r)
        except (AttributeError, TypeError):
            print("DEBUG: Skipping an invalid result:", r)
    
    if not valid_results:
        return "Error: No valid results returned from arXiv."
    
    mapping = {
        'title': lambda r: r.title,
        'abstract': lambda r: r.summary,
        'authors': lambda r: ', '.join([author.name for author in r.authors]),
        'year': lambda r: r.published.year,
        'url': lambda r: r.pdf_url,
        'source': lambda item: "arxiv"
    }
    return format_items(valid_results, mapping)

BACKENDS = {
    "semantic_scholar": semantic_scholar_search,
    "arxiv": arxiv_search,
    "crossref": crossref_search,
    "core": core_search,
}

def search_papers(query, limit=10, backend=None):
    if backend is None:
        from config import DEFAULT_SEARCH_BACKEND
        backend = DEFAULT_SEARCH_BACKEND
    if backend not in BACKENDS:
        return f"Error: Unknown backend '{backend}' specified."
    return BACKENDS[backend](query, limit)