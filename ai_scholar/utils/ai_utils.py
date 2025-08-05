import json
from typing import List, Dict, Any, Optional

def clean_ai_response(response_text: str) -> str:
    response_text = response_text.strip()
    if response_text.startswith("```json"):
        response_text = response_text.replace("```json", "").replace("```", "").strip()
    elif response_text.startswith("```"):
        response_text = response_text.replace("```", "").strip()
    return response_text

def parse_ai_response(response_text: str) -> Optional[List[Dict[str, Any]]]:
    try:
        cleaned_text = clean_ai_response(response_text)
        result = json.loads(cleaned_text)
        
        if isinstance(result, list):
            return result
        elif isinstance(result, dict) and "papers" in result:
            return result["papers"]
        else:
            return None
            
    except json.JSONDecodeError:
        return None

def is_quota_error(error: Exception) -> bool:
    error_str = str(error).lower()
    return any(indicator in error_str for indicator in [
        "quota exceeded", "rate limit", "429", "resource exhausted", "too many requests"
    ])

def create_paper_summary(paper: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "title": paper.get("title", ""),
        "authors": paper.get("authors", ""),
        "abstract": paper.get("abstract", ""),
        "publication_date": paper.get("published", ""),
        "citations": paper.get("citations", 0)
    }

def create_description_summary(paper: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "title": paper.get("title", ""),
        "authors": paper.get("authors", "")
    }

def calculate_final_score(ai_relevance: int, citations: int, citation_weight: float) -> float:
    citation_score = min(citations / 100.0, 1.0)
    final_score = (1 - citation_weight) * (ai_relevance / 10.0) + citation_weight * citation_score
    return round(final_score * 10, 1)

def validate_explanation(explanation: str, forbidden_starts: List[str] = None) -> bool:
    """Validate explanation quality and uniqueness."""
    if not explanation or len(explanation) < 20:
        return False
    
    if forbidden_starts:
        return not any(explanation.lower().startswith(start) for start in forbidden_starts)
    
    return True
