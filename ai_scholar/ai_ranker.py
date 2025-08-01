from .prompts import ai_ranking_prompt, citation_ranking_prompt, ai_description_prompt
from .ai_models import ai_models
from .config import SearchConfig
from .utils.ai_utils import create_paper_summary, create_description_summary, calculate_final_score, validate_explanation
from .utils.helpers import _safe_int_conversion, extract_arxiv_ids, update_papers_with_citations

def process_ai_batch(prompt, batch_num, total_batches, batch_type="processing"):
    try:
        return ai_models.process_batch(prompt, batch_num, total_batches, batch_type)
    except Exception:
        return None

def generate_ai_descriptions(query, papers_without_descriptions):
    if not papers_without_descriptions:
        return []
    
    batch_size = ai_models.get_optimal_batch_size("description")
    total_papers = min(len(papers_without_descriptions), SearchConfig.DEFAULT_LIMIT)
    papers_to_process = papers_without_descriptions[:total_papers]
    total_batches = (total_papers + batch_size - 1) // batch_size
    
    forbidden_starts = ["this paper", "the authors", "this work", "this research", "the paper", "this study"]
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, total_papers)
        batch_papers = papers_to_process[start_idx:end_idx]
        
        simplified_papers = [create_description_summary(paper) for paper in batch_papers]
        
        prompt = ai_description_prompt(query, simplified_papers)
        result = process_ai_batch(prompt, batch_num + 1, total_batches, "description")
        
        if result:
            for i, description_data in enumerate(result):
                if i < len(batch_papers):
                    explanation = description_data.get("explanation", "").strip()
                    if validate_explanation(explanation, forbidden_starts):
                        batch_papers[i]["explanation"] = explanation
    
    return papers_to_process

def ai_ranker(query, all_papers, ranking_mode="ai_ranking", ai_result_limit=50):
    if not all_papers:
        return []
    
    citation_weight = SearchConfig.CITATION_WEIGHT_CITATION if ranking_mode == "citation_ranking" else SearchConfig.CITATION_WEIGHT_AI
    papers_to_process = all_papers[:ai_result_limit * 2] if len(all_papers) > ai_result_limit * 2 else all_papers
    
    batch_size = ai_models.get_optimal_batch_size("ranking")
    all_ranked_papers = []
    total_papers = len(papers_to_process)
    total_batches = (total_papers + batch_size - 1) // batch_size
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, total_papers)
        batch_papers = papers_to_process[start_idx:end_idx]
        
        simplified_papers = [create_paper_summary(paper) for paper in batch_papers]
        
        prompt = ai_ranking_prompt(query, len(batch_papers), simplified_papers, batch_num + 1, total_batches, total_papers)
        ai_result = process_ai_batch(prompt, batch_num + 1, total_batches, "ranking")
        
        if ai_result:
            for i, rank_data in enumerate(ai_result):
                if i < len(batch_papers):
                    original_paper = batch_papers[i]
                    ai_relevance = _safe_int_conversion(rank_data.get("relevance_score", 5))
                    
                    final_score = calculate_final_score(
                        ai_relevance, 
                        original_paper.get("citations", 0), 
                        citation_weight
                    )
                    
                    original_paper["ai_relevance_score"] = ai_relevance
                    original_paper["final_relevance_score"] = final_score
                    original_paper["explanation"] = rank_data.get("explanation", "").strip()
                    
                    all_ranked_papers.append(original_paper)
        else:
            for paper in batch_papers:
                paper["ai_relevance_score"] = 5
                paper["final_relevance_score"] = 5.0
                paper["explanation"] = ""
                all_ranked_papers.append(paper)
    
    all_ranked_papers.sort(key=lambda x: x.get("final_relevance_score", 0), reverse=True)
    
    papers_without_descriptions = [
        paper for paper in all_ranked_papers
        if not validate_explanation(paper.get("explanation", ""))
    ]
    
    if papers_without_descriptions:
        generate_ai_descriptions(query, papers_without_descriptions)
    
    return all_ranked_papers

def fetch_paper(papers):
    return update_papers_with_citations(extract_arxiv_ids(papers))
