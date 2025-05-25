import json
import logging

from ai_ranker import ai_ranker
from paper_search import BACKENDS
from utils import  filter_results_by_year, generic_requests_search, format_items

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

def aggregate_and_rank_papers(query, limit, ai_result_limit, min_year, max_year):
    aggregated_papers = []
    logger.debug(f"Starting aggregation for query: '{query}'")
    
    for backend_name, backend_func in BACKENDS.items():
        try:
            logger.debug(f"Querying backend '{backend_name}' with query: '{query}' and limit: {limit}")
            result = backend_func(query, limit)
            logger.debug(f"Backend '{backend_name}' returned: {result}")
            
            papers = None
            if isinstance(result, dict):
                if backend_name == "arxiv":
                    papers = format_items(result.get("results", []), result.get("mapping", {}))
                else:
                    papers = generic_requests_search(
                        result.get("url"), 
                        result.get("params"), 
                        mapping=result.get("mapping"), 
                        extractor=result.get("extractor")
                    )
            elif isinstance(result, list):
                papers = result
            else:
                logger.error(f"Backend '{backend_name}' returned invalid data: {result}")
                continue
            
            if not isinstance(papers, list):
                logger.error(f"Backend '{backend_name}' did not return a list: {papers}")
                continue
            
            if not all(isinstance(paper, dict) for paper in papers):
                logger.error(f"Backend '{backend_name}' returned items that are not dictionaries: {papers}")
                continue
            
            aggregated_papers.extend(papers)
        
        except Exception as e:
            logger.error(f"Error with backend '{backend_name}': {e}")
    
    if not aggregated_papers:
        logger.warning("No papers were aggregated from any backend.")
        return []
    
    logger.debug(f"Aggregated papers before ranking: {aggregated_papers}")
    
    if min_year is not None or max_year is not None:
        aggregated_papers = filter_results_by_year(aggregated_papers, min_year, max_year)
    
    unique_papers = remove_duplicates(aggregated_papers)
    logger.debug(f"{len(unique_papers)} papers after duplicate removal.")
    
    ranked_papers = ai_ranker(query, unique_papers, ai_result_limit)
    logger.debug(f"{len(ranked_papers)} papers returned by AI ranker.")
    
    merged = merge_ranked_with_details(ranked_papers, aggregated_papers)
    logger.debug(f"{len(merged)} papers after merging ranked and aggregated details.")
    
    return merged[:ai_result_limit]

def remove_duplicates(papers):
    seen = set()
    unique = []
    for paper in papers:
        key = (paper.get('title'), paper.get('year'))
        if key not in seen:
            seen.add(key)
            unique.append(paper)
    return unique

def merge_ranked_with_details(ranked, aggregated):
    details_by_title = {
        paper.get("title", "").strip().lower(): paper
        for paper in aggregated if isinstance(paper.get("title"), str)
    }
    merged = []
    for rank_item in ranked:
        rank_title = rank_item.get("title", "").strip().lower()
        explanation = rank_item.get("explanation", "No explanation provided")
        matched_detail = None
        for key in details_by_title:
            if rank_title in key or key in rank_title:
                matched_detail = details_by_title[key]
                break
        if matched_detail:
            merged_item = matched_detail.copy()
            merged_item["explanation"] = explanation
            merged.append(merged_item)
        else:
            merged.append(rank_item)
    return merged

if __name__ == "__main__":
    query = input("Enter your search query: ")
    ranked = aggregate_and_rank_papers(query)
    print(json.dumps(ranked, indent=2))
