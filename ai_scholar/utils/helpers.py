import re
import requests
import logging

logger = logging.getLogger(__name__)

def format_items(items, mapping):
    return [{ key: func(item) for key, func in mapping.items() } for item in items]

def generic_requests_search(url, params, mapping, headers=None, extractor=None):
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 429:
        return "Error: Rate limit exceeded. Please try again later."
    elif response.status_code == 401:
        return "Error: Authentication failed. Please check your API key."
    elif response.status_code == 403:
        return "Error: Access forbidden. Your API key may not have the required permissions."
    elif response.status_code != 200:
        return f"Error: Unable to fetch papers (Status Code: {response.status_code})"
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
