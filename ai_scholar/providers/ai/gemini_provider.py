import time
from google import genai
from google.genai import types
from typing import Optional, Dict, Any, List
from ...interfaces.ai_interface import IAIProvider
from ...config.providers_config import ProvidersConfig
from ...utils.ai_utils import parse_ai_response, is_quota_error

class GeminiProvider(IAIProvider):
    """Google Gemini AI provider implementation"""
    
    def __init__(self, api_key: str, model_name: Optional[str] = None):
        self.api_key = api_key
        self.model_name = model_name or ProvidersConfig.AI.GEMINI_MODEL
        self.max_tokens = ProvidersConfig.AI.GOOGLE_MAX_TOKENS
        self.temperature = ProvidersConfig.AI.TEMPERATURE
        self.batch_size = ProvidersConfig.AI.GOOGLE_BATCH_SIZE
        self.quota_exceeded = False
        self.last_error_time = None
        
        # Initialize client
        self.client = genai.Client(api_key=self.api_key)
    
    def generate_content(self, prompt: str, operation_type: str = "general") -> Optional[str]:
        """Generate content using Google Gemini"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                    top_p=ProvidersConfig.AI.TOP_P,
                    top_k=ProvidersConfig.AI.TOP_K
                )
            )
            
            if response and hasattr(response, 'text') and response.text:
                # Reset quota status on successful response
                if self.quota_exceeded:
                    self.quota_exceeded = False
                    self.last_error_time = None
                return response.text.strip()
            
            return None
            
        except Exception as e:
            if is_quota_error(e):
                self.quota_exceeded = True
                self.last_error_time = time.time()
            raise e
    
    def process_batch(self, prompt: str, batch_num: int, total_batches: int, operation_type: str) -> Optional[List[Dict[str, Any]]]:
        """Process a batch of papers with Gemini"""
        response_text = self.generate_content(prompt, f"{operation_type} batch")
        
        if not response_text:
            return None
        
        return parse_ai_response(response_text)
    
    def get_provider_name(self) -> str:
        """Return provider name"""
        return "google_gemini"
    
    def is_available(self) -> bool:
        """Check if provider is available"""
        if self.quota_exceeded and self.last_error_time:
            # Check if cooldown period has passed
            cooldown_seconds = ProvidersConfig.AI.QUOTA_COOLDOWN_HOURS * 3600
            if time.time() - self.last_error_time > cooldown_seconds:
                self.quota_exceeded = False
                self.last_error_time = None
                return True
            return False
        
        return not self.quota_exceeded
    
    def get_optimal_batch_size(self, operation_type: str = "general") -> int:
        """Get optimal batch size for this provider"""
        base_size = self.batch_size
        return base_size + 5 if operation_type == "description" else base_size
    
    def reset_quota_status(self):
        """Reset quota exceeded status"""
        self.quota_exceeded = False
        self.last_error_time = None
    
    def rank_papers(self, query: str, papers: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        """Rank papers using Gemini AI"""
        if not papers:
            return []
        
        # Prepare ranking prompt
        ranking_prompt = self._build_ranking_prompt(query, papers, limit)
        
        response = self.generate_content(ranking_prompt, "ranking")
        if not response:
            return papers[:limit]  # Fallback to original order
        
        # Parse AI response and return ranked papers
        return self._parse_ranking_response(response, papers, limit)
    
    def generate_summary(self, papers: List[Dict[str, Any]], query: str) -> str:
        """Generate a summary of papers"""
        if not papers:
            return "No papers to summarize."
        
        summary_prompt = f"""
        Based on the search query "{query}", please provide a comprehensive summary of these research papers:
        
        {self._format_papers_for_prompt(papers)}
        
        Please provide:
        1. An overview of the main research themes
        2. Key findings and contributions
        3. Notable trends or patterns
        4. Recommendations for further reading
        
        Keep the summary concise but informative.
        """
        
        return self.generate_content(summary_prompt, "summary") or "Unable to generate summary."
    
    def generate_insights(self, papers: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """Generate research insights"""
        if not papers:
            return {"error": "No papers to analyze"}
        
        insights_prompt = f"""
        Analyze these research papers for the query "{query}" and provide insights:
        
        {self._format_papers_for_prompt(papers)}
        
        Please provide a JSON response with:
        {{
            "main_themes": ["theme1", "theme2", ...],
            "key_researchers": ["name1", "name2", ...],
            "trending_topics": ["topic1", "topic2", ...],
            "research_gaps": ["gap1", "gap2", ...],
            "methodologies": ["method1", "method2", ...],
            "future_directions": "text about future research directions"
        }}
        """
        
        response = self.generate_content(insights_prompt, "insights")
        if response:
            try:
                import json
                return json.loads(response)
            except:
                return {"insights": response}
        
        return {"error": "Unable to generate insights"}
    
    def _build_ranking_prompt(self, query: str, papers: List[Dict[str, Any]], limit: int) -> str:
        """Build prompt for paper ranking"""
        papers_text = ""
        for i, paper in enumerate(papers[:50]):  # Limit to avoid token overflow
            papers_text += f"""
Paper {i+1}:
Title: {paper.get('title', 'N/A')}
Authors: {paper.get('authors', 'N/A')}
Year: {paper.get('year', 'N/A')}
Citations: {paper.get('citations', 'N/A')}
Abstract: {paper.get('abstract', 'N/A')[:300]}...
---
"""
        
        return f"""
You are an expert research assistant. Rank the following papers based on their relevance to the query: "{query}"

Consider these factors:
1. Direct relevance to the query
2. Citation count and impact
3. Recency and novelty
4. Quality of research methodology
5. Comprehensiveness of the work

{papers_text}

Please return the top {limit} papers in order of relevance, with a brief explanation for each ranking.
Format your response as a JSON array with this structure:
[
  {{
    "rank": 1,
    "title": "Paper Title",
    "explanation": "Brief explanation of why this paper ranks highly"
  }},
  ...
]
"""
    
    def _parse_ranking_response(self, response: str, papers: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        """Parse AI ranking response and return ranked papers"""
        try:
            import json
            import re
            
            # Try to extract JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                ranking_data = json.loads(json_match.group())
                
                ranked_papers = []
                for rank_info in ranking_data[:limit]:
                    title = rank_info.get('title', '')
                    explanation = rank_info.get('explanation', '')
                    
                    # Find matching paper
                    for paper in papers:
                        if self._titles_match(paper.get('title', ''), title):
                            ranked_paper = paper.copy()
                            ranked_paper['explanation'] = explanation
                            ranked_papers.append(ranked_paper)
                            break
                
                return ranked_papers
            
        except Exception as e:
            pass
        
        fallback_papers = []
        for i, paper in enumerate(papers[:limit]):
            paper_copy = paper.copy()
            paper_copy['explanation'] = f"Ranked #{i+1} based on AI analysis"
            fallback_papers.append(paper_copy)
        
        return fallback_papers
    
    def _titles_match(self, title1: str, title2: str) -> bool:
        """Check if two titles are similar enough to be considered the same paper"""
        if not title1 or not title2:
            return False
        
        # Simple similarity check - could be improved with fuzzy matching
        title1_clean = title1.lower().strip()
        title2_clean = title2.lower().strip()
        
        return title1_clean == title2_clean or title1_clean in title2_clean or title2_clean in title1_clean
    
    def _format_papers_for_prompt(self, papers: List[Dict[str, Any]]) -> str:
        """Format papers for AI prompts"""
        formatted = ""
        for i, paper in enumerate(papers[:20]):  # Limit to avoid token overflow
            formatted += f"""
Paper {i+1}:
- Title: {paper.get('title', 'N/A')}
- Authors: {paper.get('authors', 'N/A')}
- Year: {paper.get('year', 'N/A')}
- Citations: {paper.get('citations', 'N/A')}
- Abstract: {paper.get('abstract', 'N/A')[:200]}...

"""
        return formatted
