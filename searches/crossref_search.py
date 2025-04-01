from config import CROSSREF_API_URL
from utils import generic_requests_search


def search(query, limit=10):
    params = {"query": query, "rows": limit}

    mapping = {
        'title': lambda item: item.get('title', ['No title'])[0],
        'abstract': lambda item: item.get('abstract', 'No abstract available'),
        
        'authors': lambda item: ', '.join([
        f"{author.get('given', '')} {author.get('family', '')}".strip()
        for author in item.get('author', [])
        ]) or "Unknown authors",
        
        'year': lambda item: item.get('issued', {}).get('date-parts', [[None]])[0][0],
        'url': lambda item: item.get('URL', 'No URL available'),
        'source': lambda item: "crossref",
        'citation': lambda item: item.get('is-referenced-by-count', 'N/A')

    }
    extractor = lambda r: r.json()['message']['items']
    return {
        "url": CROSSREF_API_URL,
        "params": params,
        "mapping": mapping,
        "extractor": extractor
    }
    #return generic_requests_search(CROSSREF_API_URL, params, mapping, extractor=extractor)
