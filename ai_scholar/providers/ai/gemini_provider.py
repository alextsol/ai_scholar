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
        """Generate content using Google Gemini with optimized settings"""
        try:
            # Adjust parameters based on operation type
            if operation_type == "ranking":
                # More deterministic for ranking consistency
                temperature = 0.3
                top_p = 0.9
                max_tokens = min(4000, self.max_tokens)  # Ensure we have enough tokens for detailed ranking
            else:
                temperature = self.temperature
                top_p = ProvidersConfig.AI.TOP_P
                max_tokens = self.max_tokens
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    top_p=top_p,
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
        """Build enhanced prompt for intelligent paper ranking"""
        papers_text = ""
        for i, paper in enumerate(papers[:50]):  # Limit to avoid token overflow
            abstract = (paper.get('abstract') or 'N/A')[:400] if paper.get('abstract') else 'N/A'
            citations = paper.get('citations', 'N/A')
            year = paper.get('year', 'N/A')
            
            papers_text += f"""
Paper {i+1}:
Title: {paper.get('title', 'N/A')}
Authors: {paper.get('authors', 'N/A')}
Year: {year}
Citations: {citations}
Source: {paper.get('source', 'N/A')}
Abstract: {abstract}
---
"""
        
        return f"""
You are an expert academic research assistant with deep knowledge across multiple scientific domains. Your task is to intelligently rank papers based on their relevance to the query: "{query}"

RANKING CRITERIA (in order of importance):
1. SEMANTIC RELEVANCE (40%): How directly and comprehensively does the paper address the query topic?
   - Look for exact keyword matches in title and abstract
   - Consider conceptual relevance and related concepts
   - Prefer papers that cover the core aspects of the query

2. RESEARCH QUALITY (25%): Assess the rigor and methodology
   - Clear research questions and hypotheses
   - Appropriate methodology and experimental design
   - Comprehensive literature review and citations
   - Statistical significance and validation

3. IMPACT AND CITATIONS (20%): Consider academic influence
   - Citation count relative to publication year
   - High citations indicate peer recognition
   - Recent papers with growing citation trends

4. RECENCY AND NOVELTY (10%): Balance current relevance
   - Recent papers (2020+) for emerging topics
   - Seminal older papers for established concepts
   - Novel approaches or breakthrough findings

5. COMPLETENESS (5%): Comprehensive coverage
   - Detailed abstracts indicating thorough work
   - Multiple aspects of the topic covered
   - Practical applications or implications

ANALYSIS INSTRUCTIONS:
- Read each abstract carefully to understand the actual contribution
- Consider the query context - what would be most useful for someone researching "{query}"?
- Avoid bias toward any particular source or publication year
- Look for papers that would provide the best learning path for the topic
- Consider both theoretical foundations and practical applications

PAPERS TO ANALYZE:
{papers_text}

REQUIRED OUTPUT:
Return EXACTLY the top {limit} papers ranked by overall relevance score. For each paper, provide:
1. A relevance score (1-100) based on the criteria above
2. A detailed explanation of why this paper deserves its ranking
3. Specific aspects that make it valuable for someone studying "{query}"

Format your response as a valid JSON array:
[
  {{
    "rank": 1,
    "title": "Exact title from the paper list",
    "relevance_score": 95,
    "explanation": "Detailed explanation covering: semantic relevance, research quality, impact, and why it's essential for understanding {query}. Mention specific aspects from the abstract that make it valuable."
  }},
  {{
    "rank": 2,
    "title": "Exact title from the paper list", 
    "relevance_score": 88,
    "explanation": "Detailed explanation..."
  }}
]

IMPORTANT: 
- Use the EXACT title as provided in the paper list
- Rank papers by their actual contribution to understanding "{query}", not by publication prestige
- Provide substantial explanations (50+ words) showing deep analysis
- Ensure relevance scores reflect genuine quality differences
]
"""
    
    def _parse_ranking_response(self, response: str, papers: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        """Parse AI ranking response and return ranked papers with enhanced scoring"""
        try:
            import json
            import re
            
            # Try to extract JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                ranking_data = json.loads(json_match.group())
                
                ranked_papers = []
                found_titles = set()
                
                for rank_info in ranking_data[:limit]:
                    title = rank_info.get('title', '')
                    explanation = rank_info.get('explanation', '')
                    relevance_score = rank_info.get('relevance_score', 0)
                    
                    # Find matching paper with improved matching
                    best_match = None
                    best_score = 0
                    
                    for paper in papers:
                        paper_title = paper.get('title', '')
                        if paper_title in found_titles:
                            continue
                            
                        match_score = self._calculate_title_similarity(paper_title, title)
                        if match_score > best_score and match_score > 0.7:  # Threshold for matching
                            best_match = paper
                            best_score = match_score
                    
                    if best_match:
                        ranked_paper = best_match.copy()
                        ranked_paper['explanation'] = explanation
                        ranked_paper['ai_relevance_score'] = relevance_score
                        ranked_paper['ranking_confidence'] = best_score
                        ranked_papers.append(ranked_paper)
                        found_titles.add(best_match.get('title', ''))
                
                # If we found good matches, return them
                if len(ranked_papers) >= min(3, limit):  # Need at least 3 good matches or all requested
                    return ranked_papers
            
        except Exception as e:
            # Log the error for debugging
            print(f"AI ranking parse error: {e}")
        
        # Enhanced fallback: rank by a combination of factors
        return self._fallback_ranking(papers, limit)
    
    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity score between two titles (0-1)"""
        if not title1 or not title2:
            return 0.0
        
        title1_clean = title1.lower().strip()
        title2_clean = title2.lower().strip()
        
        # Exact match
        if title1_clean == title2_clean:
            return 1.0
        
        # Substring match
        if title1_clean in title2_clean or title2_clean in title1_clean:
            return 0.9
        
        # Word overlap scoring
        words1 = set(title1_clean.split())
        words2 = set(title2_clean.split())
        
        # Remove common words that don't add meaning
        common_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words1 = words1 - common_words
        words2 = words2 - common_words
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _fallback_ranking(self, papers: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        """Intelligent fallback ranking when AI parsing fails"""
        scored_papers = []
        
        for paper in papers:
            score = 0
            
            # Citation score (0-40 points)
            citations = paper.get('citations', 0)
            if citations and citations != 'N/A':
                try:
                    cite_count = int(citations)
                    score += min(40, cite_count / 10)  # Max 40 points, 1 point per 10 citations
                except:
                    pass
            
            # Recency score (0-30 points)
            year = paper.get('year')
            if year and year != 'N/A':
                try:
                    pub_year = int(year)
                    current_year = 2024
                    age = current_year - pub_year
                    if age <= 5:
                        score += 30 - (age * 5)  # Recent papers get more points
                    elif age <= 10:
                        score += 10
                except:
                    pass
            
            # Abstract quality score (0-20 points)
            abstract = paper.get('abstract', '')
            if abstract and abstract != 'N/A' and len(abstract) > 100:
                score += 20
            elif abstract and len(abstract) > 50:
                score += 10
            
            # Title relevance (0-10 points) - basic keyword matching would go here
            # For now, just add a small random component to break ties
            import random
            score += random.uniform(0, 5)
            
            scored_papers.append((score, paper))
        
        # Sort by score and return top papers
        scored_papers.sort(key=lambda x: x[0], reverse=True)
        
        fallback_papers = []
        for i, (score, paper) in enumerate(scored_papers[:limit]):
            paper_copy = paper.copy()
            paper_copy['explanation'] = f"Ranked #{i+1} by relevance score: {score:.1f} (based on citations, recency, and content quality)"
            paper_copy['ai_relevance_score'] = int(score)
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
- Abstract: {(paper.get('abstract') or 'N/A')[:200]}...

"""
        return formatted
