from .ai_ranker import ai_ranker
from .paper_search import BACKENDS
from utils.utils import filter_results_by_year, generic_requests_search, format_items

def aggregate_and_rank_papers(query, limit, ai_result_limit, ranking_mode, min_year, max_year):
    aggregated_papers = []
    
    for backend_name, backend_func in BACKENDS.items():
        try:
            result = backend_func(query, limit)
            
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
                continue
            
            if not isinstance(papers, list) or not all(isinstance(paper, dict) for paper in papers):
                continue
            
            aggregated_papers.extend(papers)
        
        except Exception:
            continue
    
    if not aggregated_papers:
        return []
    
    if min_year is not None or max_year is not None:
        aggregated_papers = filter_results_by_year(aggregated_papers, min_year, max_year)
    
    unique_papers = remove_duplicates(aggregated_papers)
    ranked_papers = ai_ranker(query, unique_papers, ranking_mode, ai_result_limit)
    merged = merge_ranked_with_details(ranked_papers, aggregated_papers)
    
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
        rank_title = (rank_item.get("title") or rank_item.get("t", "")).strip().lower()
        rank_authors = rank_item.get("authors") or rank_item.get("a", "")
        explanation = rank_item.get("explanation", "No explanation provided")
        citation = rank_item.get("citations") or rank_item.get("c")
        
        matched_detail = None
        for key in details_by_title:
            if rank_title in key or key in rank_title:
                matched_detail = details_by_title[key]
                break
            
        if matched_detail:
            merged_item = matched_detail.copy()
            if explanation and explanation.strip() and explanation not in ["No explanation provided", "AI ranking based on relevance to query"]:
                merged_item["explanation"] = explanation
            else:
                merged_item["explanation"] = f"This paper is relevant to your query '{merged_item.get('title', 'research')}' based on content analysis and research methodology."
            
            if citation and citation not in (None, "Not available", 0, "0"):
                merged_item["citations"] = citation
            elif "citation" in matched_detail and matched_detail["citation"] and matched_detail["citation"] not in ("Not available", 0, "0"):
                merged_item["citations"] = matched_detail["citation"]
            else:
                merged_item.pop("citation", None)
                merged_item.pop("citations", None)
            
            merged.append(merged_item)
        else:
            new_item = {
                "title": rank_title.title() if rank_title else "Unknown Title",
                "authors": rank_authors if rank_authors else "Unknown Authors",
                "explanation": explanation if explanation and explanation.strip() and explanation not in ["No explanation provided", "AI ranking based on relevance to query"] else f"This research provides insights relevant to your '{rank_title or 'query'}' based on comprehensive analysis."
            }
            
            if citation and citation not in (None, "Not available", 0, "0"):
                new_item["citations"] = citation
                
            merged.append(new_item)
    return merged


