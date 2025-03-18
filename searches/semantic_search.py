import requests
from config import SEMANTIC_SCHOLAR_API_URL

def search(query, limit=10):
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
    if not isinstance(data, list):
        return f"Unexpected data format: {json_response}"
    data = [item for item in data if isinstance(item, dict)]
    
    # Local import to avoid circular dependency
    from paper_search import format_items
    mapping = {
        'title': lambda item: item.get('title', 'No title'),
        'abstract': lambda item: item.get('abstract', 'No abstract available'),
        'authors': lambda item: ', '.join([author.get('name', 'Unknown') 
                                            for author in item.get('authors', []) if isinstance(author, dict)]),
        'year': lambda item: item.get('year', 'Unknown year'),
        'url': lambda item: item.get('url', 'No URL available'),
        'source': lambda item: "semantic_scholar"
    }
    return format_items(data, mapping)
