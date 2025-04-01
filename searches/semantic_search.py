from config import SEMANTIC_SCHOLAR_API_URL
from utils import generic_requests_search

def search(query, limit=10):

    params = {
        "query": query,
        "limit": limit,
        "fields": "title,abstract,authors,year,url,citationCount"
    }

    mapping = {
        'title': lambda item: item.get('title', 'No title'),
        'abstract': lambda item: item.get('abstract', 'No abstract available'),
        'authors': lambda item: ', '.join(
            [author.get('name', 'Unknown') for author in item.get('authors', []) if isinstance(author, dict)]
        ),
        'year': lambda item: item.get('year', 'Unknown year'),
        'url': lambda item: item.get('url', 'No URL available'),
        'source': lambda item: "semantic_scholar",
        'citation': lambda item: item.get('citationCount', 'N/A')
    }

    extractor = lambda r: r.json().get('data', [])
    return {
        "url": SEMANTIC_SCHOLAR_API_URL,
        "params": params,
        "mapping": mapping,
        "extractor": extractor
    }