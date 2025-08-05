import re
import requests
import logging

logger = logging.getLogger(__name__)

def format_items(items, mapping):
    return [{ key: func(item) for key, func in mapping.items() } for item in items]

def generic_requests_search(url, params, mapping, headers=None, extractor=None):
    import warnings
    warnings.warn("generic_requests_search is deprecated. Use provider-specific implementations with proper error handling.", DeprecationWarning)
    
    from ai_scholar.utils.exceptions import create_api_error
    
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 429:
        raise create_api_error("generic", 429, "Rate limit exceeded")
    elif response.status_code == 401:
        raise create_api_error("generic", 401, "Authentication failed")
    elif response.status_code == 403:
        raise create_api_error("generic", 403, "Access forbidden")
    elif response.status_code != 200:
        raise create_api_error("generic", response.status_code, f"HTTP {response.status_code}")
    
    data = extractor(response) if extractor else response.json()
    return format_items(data, mapping)

def filter_results_by_year(papers, min_year=None, max_year=None):
    if min_year is None and max_year is None:
        return papers
    
    filtered_papers = []
    for paper in papers:
        try:
            year_val = paper.get('year', 0)
            year = int(year_val) if year_val is not None else 0
            if (min_year is None or year >= min_year) and (max_year is None or year <= max_year):
                filtered_papers.append(paper)
        except (ValueError, TypeError):
            continue
    return filtered_papers

def _safe_int_conversion(value):
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        if value.lower() in ['not available', 'n/a', '', 'none']:
            return 0
        try:
            return int(value)
        except ValueError:
            return 0
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0

def extract_arxiv_ids(papers):
    for paper in papers:
        if not isinstance(paper, dict) or 'url' not in paper:
            continue
            
        url = paper.get('url', '')
        if 'arxiv' in url:
            match = re.search(r'/([^/]+?)(?:v\d+)?/?$', url)
            if match:
                paper['roi'] = match.group(1)
    return papers
