import requests
from config import CROSSREF_API_URL

def search(query, limit=10):
    params = {"query": query, "rows": limit}
    
    from paper_search import format_items, generic_requests_search
    mapping = {
        'title': lambda item: item.get('title', ['No title'])[0],
        'abstract': lambda item: item.get('abstract', 'No abstract available'),
        'authors': lambda item: ', '.join([
            f"{author.get('given', '')} {author.get('family', '')}".strip()
            for author in item.get('author', [])
        ]),
        'year': lambda item: item.get('issued', {}).get('date-parts', [[None]])[0][0],
        'url': lambda item: item.get('URL', 'No URL available'),
        'source': lambda item: "crossref"
    }
    extractor = lambda r: r.json()['message']['items']
    return generic_requests_search(CROSSREF_API_URL, params, mapping, extractor=extractor)
