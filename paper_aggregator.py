import json
import logging
from ai_ranker import deepseek_rank_papers
from paper_search import BACKENDS

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

def aggregate_and_rank_papers(query, limit=10):

    aggregated_papers = []
    logger.debug(f"Starting aggregation for query: '{query}'")
    
    for backend_name, backend_func in BACKENDS.items():
        try:
            papers = backend_func(query, limit)
            if isinstance(papers, str) or not papers:
                logger.debug(f"Skipping backend '{backend_name}': no valid papers returned.")
                continue
            logger.debug(f"Backend '{backend_name}' returned {len(papers)} papers.")
            aggregated_papers.extend(papers)
        except Exception as e:
            logger.error(f"Error with backend '{backend_name}': {e}")
    
    if not aggregated_papers:
        logger.debug("No aggregated papers found from any backend.")
        return []
    
    ranked_papers = rank_and_remove_duplicates(query, aggregated_papers)
    logger.debug(f"{len(ranked_papers)} papers after ranking and duplicate removal.")
    
    return ranked_papers[:10]


def rank_and_remove_duplicates(query, papers):
    seen = set()
    unique_papers = []
    for paper in papers:
        key = (paper.get('title'), paper.get('year'))
        if key not in seen:
            seen.add(key)
            unique_papers.append(paper)
    
    ranked = deepseek_rank_papers(query, unique_papers)
    return ranked


def merge_ranked_with_details(ranked, aggregated):
    """
    Merge ranked results (which contain only 'title' and 'explanation')
    with full details from aggregated papers based on matching titles.
    """
    # Build a lookup dict with lower-case stripped titles as keys.
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