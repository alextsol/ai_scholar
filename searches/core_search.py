import requests
from config import CORE_API_URL, CORE_API_KEY
from utils import generic_requests_search

def search(query, limit=10):
    params = {"q": query, "limit": limit}
    headers = {"Authorization": f"Bearer {CORE_API_KEY}"}
    
    mapping = {
        'title': lambda item: item.get('title', 'No title'),
        'abstract': lambda item: item.get('abstract', 'No abstract available'),
        'authors': lambda item: ', '.join(
            [author.get('name', 'Unknown') if isinstance(author, dict) else str(author)
             for author in item.get('authors', [])]
        ),
        'year': lambda item: item.get('yearPublished', 'Unknown year'),
        'url': lambda item: item.get('downloadUrl', 'No URL available'),
        'citation': lambda item: item.get('citationCount', 'N/A'),
        'source': lambda item: "core"
    }
    
    extractor = lambda r: r.json().get('results', [])
    return generic_requests_search(CORE_API_URL, params, mapping, headers=headers, extractor=extractor)
