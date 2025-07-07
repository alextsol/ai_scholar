
def format_items(items, mapping):
    return [{ key: func(item) for key, func in mapping.items() } for item in items]

def generic_requests_search(url, params, mapping, headers=None, extractor=None):
    import requests
    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
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
    """Safely convert citation values to integers"""
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