import os
from utils.utils import generic_requests_search
from dotenv import load_dotenv

load_dotenv()

def search(query, limit, min_year=None, max_year=None):
    params = {"q": query, "limit": limit}
    headers = {"Authorization": f"Bearer {os.getenv('CORE_API_KEY')}"}
    
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
        'authors': lambda item: ', '.join([author.get('name', 'Unknown author') if isinstance(author, dict) else str(author) for author in item.get('authors', [])]),
        'year': lambda item: item.get('yearPublished', 'Unknown year'),
        'url': lambda item: item.get('downloadUrl', 'No URL available'),
        'citation': lambda item: item.get('citationCount', 'N/A'),
        'source': lambda item: "core"
    }
    
    extractor = lambda r: r.json().get('results', [])
    
    return generic_requests_search(
        os.getenv("CORE_API_URL", "https://api.core.ac.uk/v3/search/works"), 
        params, 
        mapping, 
        headers=headers, 
        extractor=extractor
    )
