
import json
import re
from venv import logger

import requests

from config import OPENROUTER_API_KEY, OPENROUTER_API_URL
from prompts import ai_ranking, citation_ranking


def ai_ranker(query, papers, ranking_mode, ai_result_limit=10):
    papers = fetch_paper(papers);
    simplified_papers = [
        {
            "t": paper.get("title", "No title"),
            "a": paper.get("authors", "No authors")
        }
        for paper in papers if isinstance(paper, dict)
    ]
    #papers_json = json.dumps(simplified_papers, indent=2)
    
    if(ranking_mode == "ai"):
        papers_json = json.dumps(simplified_papers, indent=2)
        prompt = ai_ranking(query, ai_result_limit, papers_json)
    else:
        #papers = fetch_citation_counts(papers,999)
        simplified_papers = [
            {
            "t": paper.get("title", "No title"),
            "a": paper.get("authors", "No authors"),
            "c": paper.get("citation", 0) or 0
            }
            for paper in papers if isinstance(paper, dict)
        ]
        
        simplified_papers = sorted(simplified_papers, key=lambda x: x.get('c', 0) or 0, reverse=True)

        papers_json = json.dumps(simplified_papers, indent=2)
        prompt = citation_ranking(query, ai_result_limit, papers_json)
    
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
            try:
                limit = int(ai_result_limit)
                return papers[:limit] if limit > 0 else papers
            except (ValueError, TypeError):
                return papers

        data = response.json()
        message_content = data["choices"][0]["message"]["content"]
        message_content = re.sub(r"^```json\s*", "", message_content)
        message_content = re.sub(r"\s*```$", "", message_content)
        
        if not message_content.strip():
            logger.error("AI response content is empty.")
            try:
                limit = int(ai_result_limit)
                return papers[:limit] if limit > 0 else papers
            except (ValueError, TypeError):
                return papers

        try:
            ranked_papers = json.loads(message_content)
            limit = int(ai_result_limit)
            return ranked_papers[:limit] if limit > 0 else ranked_papers
        
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.error(f"Failed to parse AI response as JSON: {e}. Content was: {message_content}")
            try:
                limit = int(ai_result_limit)
                return papers[:limit] if limit > 0 else papers
            except (ValueError, TypeError):
                return papers
    except Exception as e:
        logger.error(f"Exception occurred during AI ranking: {e}")
        try:
            limit = int(ai_result_limit)
            return papers[:limit] if limit > 0 else papers
        except (ValueError, TypeError):
            return papers
        
        
def fetch_paper(papers):
    """
    Extract arXiv IDs from paper URLs and add them to paper objects
    """
    for paper in papers:
        if not isinstance(paper, dict) or 'url' not in paper:
            continue
            
        url = paper.get('url', '')
        if 'arxiv' in url:
            # Extract arXiv ID from URL
            match = re.search(r'/([^/]+?)(?:v\d+)?/?$', url)
            if match:
                paper['roi'] = match.group(1)  # roi = research object identifier
            
    return update_papers_with_citations(papers)

def update_papers_with_citations(papers):
    import time
    import requests

    BATCH_SIZE = 25  # Semantic Scholar allows up to 100 per batch
    DELAY = 1  # Seconds between batches to respect rate limits

    # Map arXiv IDs to their index in the papers list
    arxiv_id_to_index = {}
    arxiv_ids = []
    for idx, paper in enumerate(papers):
        if not isinstance(paper, dict):
            continue
        arxiv_id = paper.get('roi')
        if arxiv_id:
            arxiv_ids.append(arxiv_id)
            arxiv_id_to_index[arxiv_id] = idx

    if not arxiv_ids:
        return papers

    headers = {
        'Content-Type': 'application/json'
    }

    for i in range(0, len(arxiv_ids), BATCH_SIZE):
        batch_ids = arxiv_ids[i:i + BATCH_SIZE]
        payload = {
            "ids": [f"ARXIV:{arxiv_id}" for arxiv_id in batch_ids]
        }
        try:
            response = requests.post(
                "https://api.semanticscholar.org/graph/v1/paper/batch?fields=title,citationCount,externalIds",
                json=payload,
                headers=headers,
                timeout=15
            )
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    paper_list = data
                elif isinstance(data, dict) and 'data' in data and isinstance(data['data'], list):
                    paper_list = data['data']
                else:
                    logger.error(f"Unexpected response format: {data}")
                    continue
                
                for paper_data in paper_list:
                    if not paper_data:
                        continue
                    arxiv_id = None
                    external_ids = paper_data.get('externalIds', {})
                    if 'arxiv' in external_ids:
                        arxiv_id = external_ids['arxiv'][0] if isinstance(external_ids['arxiv'], list) else external_ids['arxiv']
           
                    # Fallback: match by title if arxiv_id is missing
                    if not arxiv_id:
                        title = paper_data.get('title', '').strip().lower()
                        for aid, idx in arxiv_id_to_index.items():
                            if papers[idx].get('title', '').strip().lower() == title:
                                arxiv_id = aid
                                break
                    citation_count = paper_data.get('citationCount', 0)
                    if arxiv_id:
                        idx = arxiv_id_to_index.get(arxiv_id)
                        if idx is not None:
                            papers[idx]['citation'] = int(citation_count)
            else:
                logger.error(f"Semantic Scholar API Error for batch {i//BATCH_SIZE+1}: {response.status_code}, {response.text}")
        except Exception as e:
            logger.error(f"Semantic Scholar Exception for batch {i//BATCH_SIZE+1}: {e}")

        if i + BATCH_SIZE < len(arxiv_ids):
            time.sleep(DELAY)

    return papers