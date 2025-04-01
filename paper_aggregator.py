from asyncio.log import logger
import json

from ai_ranker import ai_rank_papers
from paper_search import BACKENDS
from utils import generic_requests_search, format_items

def aggregate_and_rank_papers(query, limit=10):
    """
    Aggregates papers from multiple backends, removes duplicates, and ranks them.
    """
    aggregated_papers = []
    
    for backend_name, backend_func in BACKENDS.items():
        try:
            logger.debug(f"Querying backend '{backend_name}' with query: '{query}' and limit: {limit}")
            result = backend_func(query, limit)
            logger.debug(f"Backend '{backend_name}' returned: {result}")
            
            papers = None
            # If the backend returns a dict (as with CORE), process it
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
    ranked_papers = rank_and_remove_duplicates(query, aggregated_papers)
    logger.debug(f"{len(ranked_papers)} papers after ranking and duplicate removal.")
    
    return ranked_papers[:10]

def rank_and_remove_duplicates(query, papers):
    # Remove duplicates
    
    logger.debug(f"Ranking papers with query: '{query}' and papers: {papers}")

    seen = set()
    unique_papers = []
    for paper in papers:
        key = (paper.get('title'), paper.get('year'))
        if key not in seen:
            seen.add(key)
            unique_papers.append(paper)
    # Rank papers using your AI ranker
    ranked = ai_rank_papers(query, unique_papers)
    return ranked

def merge_ranked_with_details(ranked, aggregated):
    details_by_title = {
        paper.get("title", "").strip().lower(): paper
        for paper in aggregated if isinstance(paper.get("title"), str)
    }
    merged = []
    for rank_item in ranked:
        rank_title = rank_item.get("title", "").strip().lower()
        explanation = rank_item.get("explanation", "")
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
