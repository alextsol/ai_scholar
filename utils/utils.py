import re
import requests
import logging
from .arxvic_configs.semantic_scholar_api import SemanticScholarAPI
from .arxvic_configs.citation_matcher import CitationMatcher
from .arxvic_configs.paper_indexer import PaperIndexer

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

def update_papers_with_citations(papers):
    if not PaperIndexer.has_arxiv_papers(papers):
        return papers
    
    arxiv_ids, arxiv_id_to_index = PaperIndexer.create_arxiv_index(papers)
    
    api = SemanticScholarAPI()
    papers_data = api.fetch_all_papers(arxiv_ids)
    
    _update_citations_from_data(papers, papers_data, arxiv_id_to_index)
    
    return papers

def _update_citations_from_data(papers, papers_data, arxiv_id_to_index):
    for paper_data in papers_data:
        if not paper_data:
            continue
        
        arxiv_id = CitationMatcher.extract_arxiv_id_from_paper(paper_data)
        
        if not arxiv_id:
            arxiv_id = CitationMatcher.match_by_title(paper_data, papers, arxiv_id_to_index)
        
        if arxiv_id:
            citation_count = paper_data.get('citationCount', 0)
            CitationMatcher.update_paper_citation(papers, arxiv_id_to_index, arxiv_id, citation_count)
                       
def generate_fallback_explanation(query, paper_title="", paper_authors=""):
    title_lower = paper_title.lower() if paper_title else ""
    query_lower = query.lower()
    
    if not title_lower:
        return f"This research work contributes specialized methodologies and theoretical frameworks applicable to '{query}' investigations."
    
    if "automation" in title_lower:
        return f"This paper presents '{paper_title}', introducing automation frameworks and tools that streamline processes in '{query}' research domains."
    elif "methodology" in title_lower or "method" in title_lower:
        return f"'{paper_title}' develops specific methodological approaches and procedural frameworks that advance '{query}' research practices."
    elif "tool" in title_lower:
        return f"This work introduces '{paper_title}', presenting specialized tools and software solutions for addressing '{query}' challenges."
    elif "review" in title_lower or "survey" in title_lower:
        return f"'{paper_title}' provides comprehensive analysis and systematic review of current approaches in '{query}', offering strategic insights for researchers."
    elif "comparison" in title_lower or "comparative" in title_lower:
        return f"This paper presents '{paper_title}', conducting comparative analysis that evaluates different approaches within '{query}' research."
    elif "adaptive" in title_lower or "optimization" in title_lower:
        return f"'{paper_title}' introduces adaptive algorithms and optimization techniques specifically designed for '{query}' applications."
    elif "testing" in title_lower and "test" in query_lower:
        return f"This research focuses on '{paper_title}', developing specialized testing methodologies and validation frameworks for '{query}' systems."
    elif "algorithm" in title_lower:
        return f"'{paper_title}' presents novel algorithmic solutions and computational approaches for solving '{query}' problems."
    elif "analysis" in title_lower:
        return f"This work conducts '{paper_title}', providing analytical frameworks and evaluation methods for '{query}' research."
    elif "model" in title_lower or "modeling" in title_lower:
        return f"'{paper_title}' develops mathematical models and simulation frameworks applicable to '{query}' investigations."
    elif "system" in title_lower:
        return f"This paper describes '{paper_title}', architecting system-level solutions for '{query}' applications."
    elif "performance" in title_lower:
        return f"'{paper_title}' evaluates performance characteristics and optimization strategies relevant to '{query}' implementations."
    elif "design" in title_lower:
        return f"This research presents '{paper_title}', offering design principles and architectural approaches for '{query}' systems."
    elif "framework" in title_lower:
        return f"'{paper_title}' establishes comprehensive frameworks and structural approaches for advancing '{query}' research."
    else:
        # Extract key nouns from title for more specific explanation
        title_words = [word for word in title_lower.split() if len(word) > 3]
        if title_words:
            key_concept = title_words[0] if title_words else "research"
            return f"'{paper_title}' focuses on {key_concept}-based approaches and specialized techniques that directly advance '{query}' research objectives."
        else:
            return f"This specialized research work '{paper_title}' contributes domain-specific knowledge and technical approaches to '{query}' investigations."
