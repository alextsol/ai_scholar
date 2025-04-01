import requests
from config import CORE_API_URL, CORE_API_KEY
from utils import generic_requests_search

def search(query, limit=10, min_year=None, max_year=None):
    params = {"q": query, "limit": limit}
    headers = {"Authorization": f"Bearer {CORE_API_KEY}"}
    
    filters = []
    if min_year:
        filters.append(f"from-pub-date:{min_year}")
    if max_year:
        filters.append(f"until-pub-date:{max_year}")
    if filters:
        params["filter"] = ",".join(filters)
    
    mapping = {
        'title': lambda item: item.get('title', 'No title'),
        'abstract': lambda item: item.get('abstract', 'No abstract available'),
        'authors': lambda item: ', '.join(item.get('authors', [])),
        'year': lambda item: item.get('yearPublished', 'Unknown year'),
        'url': lambda item: item.get('downloadUrl', 'No URL available'),
        'citation': lambda item: item.get('citationCount', 'N/A'),
        'source': lambda item: "core"
    }
    
    extractor = lambda r: r.json().get('results', [])
    
    return generic_requests_search(CORE_API_URL, params, mapping, headers=headers, extractor=extractor)
