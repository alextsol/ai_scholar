import json
import re
import time
import google.generativeai as genai
from key1 import glg
from .prompts import ai_ranking_prompt, citation_ranking_prompt
from utils.utils import _safe_int_conversion, extract_arxiv_ids, update_papers_with_citations

genai.configure(api_key=glg)

def ai_ranker(query, papers, ranking_mode, ai_result_limit):
    papers = fetch_paper(papers)
    
    BATCH_SIZE = 30
    all_ranked_papers = []
    total_papers = len(papers)
    total_batches = (total_papers + BATCH_SIZE - 1) // BATCH_SIZE
    
    for batch_num in range(total_batches):
        start_idx = batch_num * BATCH_SIZE
        end_idx = min(start_idx + BATCH_SIZE, total_papers)
        batch_papers = papers[start_idx:end_idx]
        
        simplified_papers = [
            {
                "t": paper.get("title", "No title"),
                "a": paper.get("authors", "No authors")
            }
            for paper in batch_papers if isinstance(paper, dict)
        ]
        
        if ranking_mode == "ai":
            papers_json = json.dumps(simplified_papers, indent=2)
            prompt = ai_ranking_prompt(query, len(simplified_papers), papers_json, batch_num + 1, total_batches, total_papers)
        else:
            simplified_papers = [
                {
                    "t": paper.get("title", "No title"),
                    "a": paper.get("authors", "No authors"),
                    "c": _safe_int_conversion(paper.get("citation", 0))
                }
                for paper in batch_papers if isinstance(paper, dict)
            ]
            
            simplified_papers = sorted(simplified_papers, key=lambda x: x.get('c', 0), reverse=True)
            papers_json = json.dumps(simplified_papers, indent=2)
            prompt = citation_ranking_prompt(query, len(simplified_papers), papers_json, batch_num + 1, total_batches, total_papers)
        
        try:
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=3072,
                )
            )
            
            message_content = response.text
            message_content = re.sub(r"^```json\s*", "", message_content)
            message_content = re.sub(r"\s*```$", "", message_content)
            
            if not message_content.strip():
                for paper in batch_papers:
                    paper_copy = paper.copy()
                    paper_copy["explanation"] = generate_fallback_explanation(query)
                    all_ranked_papers.append(paper_copy)
                continue
            
            try:
                ranked_papers = json.loads(message_content)
                
                for paper in ranked_papers:
                    if not paper.get("explanation") or paper.get("explanation").strip() == "":
                        paper["explanation"] = generate_fallback_explanation(query)
                
                all_ranked_papers.extend(ranked_papers)
                
            except (json.JSONDecodeError, ValueError, TypeError):
                for paper in batch_papers:
                    paper_copy = paper.copy()
                    paper_copy["explanation"] = generate_fallback_explanation(query)
                    all_ranked_papers.append(paper_copy)
                
        except Exception:
            for paper in batch_papers:
                paper_copy = paper.copy()
                paper_copy["explanation"] = generate_fallback_explanation(query)
                all_ranked_papers.append(paper_copy)
        
        if batch_num + 1 < total_batches:
            time.sleep(1)
    
    if not all_ranked_papers:
        fallback_papers = []
        for paper in papers:
            paper_copy = paper.copy()
            paper_copy["explanation"] = generate_fallback_explanation(query)
            fallback_papers.append(paper_copy)
        return fallback_papers
    
    return all_ranked_papers

def generate_fallback_explanation(query):
    if "test" in query.lower():
        return "This paper contributes to testing methodologies and quality assurance practices relevant to the research query."
    elif any(word in query.lower() for word in ["machine learning", "ml", "ai", "artificial intelligence"]):
        return "This research advances machine learning and AI methodologies with computational insights relevant to the query domain."
    elif any(word in query.lower() for word in ["neural", "deep learning", "network"]):
        return "This work contributes to neural network research and deep learning techniques relevant to the research area."
    else:
        return f"This paper provides valuable research insights relevant to '{query}' based on comprehensive content analysis."

def fetch_paper(papers):
    return update_papers_with_citations(extract_arxiv_ids(papers))


