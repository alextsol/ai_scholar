from ai_scholar.config import CROSSREF_API_URL
from utils.utils import generic_requests_search


def search(query, limit, min_year=None, max_year=None):
    params = {"query": query, "rows": limit}
    
    filters = []
    if min_year:
        filters.append(f"from-pub-date:{min_year}")
    if max_year:
        filters.append(f"until-pub-date:{max_year}")
    if filters:
        params["filter"] = ",".join(filters)
    
    mapping = {
        'title': lambda item: item.get('title', ['No title'])[0],
        'abstract': lambda item: item.get('abstract', 'No abstract available'),
        'authors': lambda item: ', '.join([
            f"{author.get('given', '')} {author.get('family', '')}".strip()
            for author in item.get('author', [])
        ]),
        'year': lambda item: item.get('issued', {}).get('date-parts', [[None]])[0][0],
        'url': lambda item: item.get('URL', 'No URL available'),
        'citation': lambda item: item.get('is-referenced-by-count', 'N/A'),
        'source': lambda item: "crossref"
    }
    extractor = lambda r: r.json()['message']['items']
    return generic_requests_search(CROSSREF_API_URL, params, mapping, extractor=extractor)
