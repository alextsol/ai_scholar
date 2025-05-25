
import json
import re
from venv import logger

import requests

from config import OPENROUTER_API_KEY, OPENROUTER_API_URL


def ai_ranker(query, papers, ai_result_limit=10):
    simplified_papers = [
        {
            "title": paper.get("title", "No title"),
            "authors": paper.get("authors", "No authors")
        }
        for paper in papers if isinstance(paper, dict)
    ]
    papers_json = json.dumps(simplified_papers, indent=2)
    
    prompt = (
        f"Based on the query '{query}', review the following list of paper titles and authors, and select the top '{ai_result_limit}' most relevant papers. "
        "For each selected paper, provide a brief explanation of its relevance. "
        "Return your answer as a JSON array of objects with the keys 'title', 'authors', and 'explanation'.\n\n"
        f"Papers:\n{papers_json}"
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
            return papers[:ai_result_limit]
        
        data = response.json()
        message_content = data["choices"][0]["message"]["content"]
        message_content = re.sub(r"^```json\s*", "", message_content)
        message_content = re.sub(r"\s*```$", "", message_content)
        ranked_papers = json.loads(message_content)
        return ranked_papers[:ai_result_limit]
    except Exception as e:
        logger.error(f"Exception during DeepSeek ranking: {e}")
        return papers[:ai_result_limit]