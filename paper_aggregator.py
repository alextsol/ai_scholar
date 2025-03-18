import requests
import json
import re
import logging
from paper_search import BACKENDS
from config import OPENROUTER_API_KEY, OPENROUTER_API_URL

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

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
    
    aggregated_papers = remove_duplicates(aggregated_papers)
    logger.debug(f"{len(aggregated_papers)} papers after duplicate removal.")
    
    ranked = deepseek_rank_papers(query, aggregated_papers)
    logger.debug(f"{len(ranked)} papers after ranking.")
    
    merged = merge_ranked_with_details(ranked, aggregated_papers)
    return merged[:10]

def deepseek_rank_papers(query, papers):
    # Simplify: send only titles to reduce token count.
    simplified_papers = [{"title": paper.get("title", "No title")} for paper in papers if isinstance(paper, dict)]
    papers_json = json.dumps(simplified_papers, indent=2)
    
    prompt = (
        f"Based on the query '{query}', review the following paper titles and select the top 10 most relevant papers. "
        "For each selection, provide a brief explanation of its relevance. Return your answer as a JSON array of objects with keys "
        "'title' and 'explanation'.\n\nPapers:\n" + papers_json
    )
    
    payload = {
        "model": "deepseek/deepseek-r1:free",
        "messages": [
            {"role": "system", "content": "You are DeepSeek, an AI assistant for ranking scholarly papers."},
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            url=OPENROUTER_API_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=10
        )
        if response.status_code != 200:
            logger.error(f"OpenRouter API error: {response.status_code}")
            return papers[:10]
        
        data = response.json()
        message_content = data["choices"][0]["message"]["content"]
        message_content = re.sub(r"^```json\s*", "", message_content)
        message_content = re.sub(r"\s*```$", "", message_content)
        ranked_papers = json.loads(message_content)
        return ranked_papers[:10]
    except Exception as e:
        logger.error(f"Exception during DeepSeek ranking: {e}")
        return papers[:10]

def merge_ranked_with_details(ranked, aggregated):
    details_by_title = {
        paper.get("title", "").strip().lower(): paper
        for paper in aggregated if isinstance(paper.get("title"), str)
    }
    merged = []
    for rank_item in ranked:
        rank_title = rank_item.get("title", "").strip().lower()
        explanation = rank_item.get("explanation", "")
        matched_detail = next(
            (details_by_title[t] for t in details_by_title if t in rank_title or rank_title in t),
            None
        )
        if matched_detail:
            merged_item = matched_detail.copy()
            merged_item["explanation"] = explanation
            merged.append(merged_item)
        else:
            merged.append(rank_item)
    return merged

def remove_duplicates(papers):
    seen = set()
    unique_papers = []
    for paper in papers:
        key = (paper.get('title'), paper.get('year'))
        if key not in seen:
            seen.add(key)
            unique_papers.append(paper)
    return unique_papers

if __name__ == "__main__":
    query = input("Enter your search query: ")
    ranked = aggregate_and_rank_papers(query)
    print(json.dumps(ranked, indent=2))
