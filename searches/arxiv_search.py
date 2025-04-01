import arxiv

from utils import format_items

def search(query, limit=10):
    search_obj = arxiv.Search(query=query, max_results=limit, sort_by=arxiv.SortCriterion.Relevance)
    results = list(search_obj.results())
    
    mapping = {
        'title': lambda r: r.title,
        'abstract': lambda r: r.summary,
        'authors': lambda r: ', '.join([author.name for author in r.authors]),
        'year': lambda r: r.published.year,
        'url': lambda r: r.pdf_url,
        'citation': lambda r: 'Not available',
        'source': lambda r: "arxiv"
    }
    return format_items(results, mapping)
