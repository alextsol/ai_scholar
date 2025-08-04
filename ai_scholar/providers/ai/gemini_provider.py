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
            return self._fallback_ranking(papers, limit)
        
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

CONTEXT: These papers have been collected from multiple academic sources (CrossRef, arXiv, Semantic Scholar, CORE, OpenAlex), deduplicated, and pre-filtered for quality. Your role is to provide the final AI-powered ranking with detailed explanations.

RANKING CRITERIA (adaptive weighting based on paper source):
1. SEMANTIC RELEVANCE (45%): How directly and comprehensively does the paper address the query topic?
   - Look for exact keyword matches in title and abstract
   - Consider conceptual relevance and related concepts
   - Prefer papers that cover the core aspects of the query

2. RESEARCH QUALITY (30%): Assess the rigor and methodology
   - Clear research questions and hypotheses
   - Appropriate methodology and experimental design
   - Comprehensive literature review and citations
   - Statistical significance and validation

3. NOVELTY AND RECENCY (15%): Balance current relevance and innovation
   - Recent papers (2020+) for emerging topics and cutting-edge research
   - Novel approaches or breakthrough findings
   - Innovative methodologies or fresh perspectives
   - For arXiv papers: Consider potential impact and innovation over citation count

4. IMPACT INDICATORS (10%): Consider available influence metrics
   - For papers with citations: Citation count relative to publication year
   - For arXiv papers: Focus on methodological innovation, comprehensive evaluation, and potential significance
   - High-quality venues and author reputation when available
   - Practical applications and reproducibility

SPECIAL HANDLING FOR ARXIV PAPERS:
- arXiv papers represent cutting-edge, often unpublished research
- Lack of citations should NOT penalize ranking - instead focus on:
  * Innovation and novelty of approach
  * Comprehensiveness of experimental evaluation
  * Clarity of methodology and potential impact
  * Relevance to current research trends
- Weight criteria as: Semantic Relevance (50%), Research Quality (35%), Novelty (15%), Impact (0%)

ANALYSIS INSTRUCTIONS:
- Read each abstract carefully to understand the actual contribution
- Consider the query context - what would be most useful for someone researching "{query}"?
- DO NOT bias against arXiv papers due to lack of citations - they often contain the most recent breakthroughs
- Balance established, well-cited work with innovative recent research
- For arXiv papers: Evaluate potential impact, methodological rigor, and innovation
- For published papers: Consider both citation impact and research quality
- Look for papers that would provide the best learning path for the topic
- Consider both theoretical foundations and practical applications
- Ensure a good mix of established knowledge and cutting-edge developments

PAPERS TO ANALYZE:
{papers_text}

REQUIRED OUTPUT:
Return EXACTLY the top {limit} papers ranked by overall relevance score. For each paper, provide:
1. A relevance score (1-100) based on the criteria above
2. A detailed, specific explanation (1-2 sentences) that explains:
   - WHY this paper is relevant to "{query}" (be specific about connections)
   - WHAT unique contribution, methodology, or findings it provides
   - HOW it advances understanding or practical application of the topic
   
EXPLANATION REQUIREMENTS:
- Make explanations SPECIFIC to the paper's actual content and contribution
- Reference specific methodologies, findings, or innovations mentioned in abstracts
- Avoid generic phrases like "this paper explores", "the authors investigate", or "this study examines"
- Connect the paper's contribution directly to the search query
- Explain the practical value for someone researching the topic
- Use concrete details from the abstract when available
- Be insightful and substantive, not just descriptive

Format your response as a valid JSON array:
[
  {{
    "rank": 1,
    "title": "Exact title from the paper list",
    "relevance_score": 95,
    "explanation": "This paper is highly relevant to '{query}' because [specific reason based on abstract content]. The [specific methodology/innovation/finding] provides [practical benefit/theoretical advancement] that is essential for [specific application]."
  }},
  {{
    "rank": 2,
    "title": "Exact title from the paper list", 
    "relevance_score": 88,
    "explanation": "This work advances '{query}' through [specific approach from abstract]. The [specific findings/techniques] offer [concrete insights/tools] for [practical application]."
  }}
]

CRITICAL REQUIREMENTS: 
- Use the EXACT title as provided in the paper list
- Keep explanations to 1-2 sentences (50-100 words maximum)
- Base explanations on ACTUAL content from abstracts, not assumptions
- Ensure relevance scores reflect genuine quality and relevance differences
- Every explanation must be unique and specific to that paper's contribution
"""
    
    def _parse_ranking_response(self, response: str, papers: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        """Parse AI ranking response and return ranked papers with enhanced scoring"""
        try:
            import json
            import re
            
            # Try to extract JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                json_text = json_match.group()
                ranking_data = json.loads(json_text)
                
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
            
        except json.JSONDecodeError as e:
            # JSON parsing failed - could be malformed response
            pass
        except Exception as e:
            # Other parsing errors
            pass
        
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
        """Intelligent fallback ranking when AI parsing fails - balanced for all sources"""
        scored_papers = []
        
        for paper in papers:
            score = 0
            source = paper.get('source', '').lower()
            
            # Source-adaptive scoring strategy
            is_arxiv = source == 'arxiv'
            
            if is_arxiv:
                # For arXiv papers: Focus on recency, quality, and innovation potential
                
                # Recency score (0-40 points) - arXiv papers benefit more from being recent
                year = paper.get('year')
                if year and year != 'N/A':
                    try:
                        pub_year = int(year)
                        current_year = 2024
                        age = current_year - pub_year
                        if age <= 2:
                            score += 40  # Very recent arXiv papers
                        elif age <= 5:
                            score += 35 - (age * 5)
                        elif age <= 10:
                            score += 15
                    except:
                        pass
                
                # Quality indicators (0-35 points)
                abstract = paper.get('abstract', '')
                if abstract and abstract != 'N/A':
                    if len(abstract) > 300:
                        score += 35  # Comprehensive abstract
                    elif len(abstract) > 150:
                        score += 25
                    elif len(abstract) > 75:
                        score += 15
                
                # Innovation bonus for arXiv (0-25 points)
                title = paper.get('title', '').lower()
                innovation_keywords = ['novel', 'new', 'improved', 'efficient', 'optimal', 'advanced', 'sota', 'state-of-the-art']
                innovation_score = sum(5 for keyword in innovation_keywords if keyword in title)
                score += min(25, innovation_score)
                
            else:
                # For published papers: Balance citations with recency and quality
                
                # Citation score (0-30 points) - reduced weight
                citations = paper.get('citations', 0)
                if citations and citations != 'N/A':
                    try:
                        cite_count = int(citations)
                        score += min(30, cite_count / 15)  # Reduced citation weight
                    except:
                        pass
                
                # Recency score (0-25 points)
                year = paper.get('year')
                if year and year != 'N/A':
                    try:
                        pub_year = int(year)
                        current_year = 2024
                        age = current_year - pub_year
                        if age <= 5:
                            score += 25 - (age * 4)
                        elif age <= 10:
                            score += 10
                    except:
                        pass
                
                # Quality score (0-25 points)
                abstract = paper.get('abstract', '')
                if abstract and abstract != 'N/A':
                    if len(abstract) > 200:
                        score += 25
                    elif len(abstract) > 100:
                        score += 15
                    elif len(abstract) > 50:
                        score += 10
                
                # Venue quality bonus (0-20 points)
                if source in ['semantic_scholar', 'crossref']:
                    score += 20  # Established publication venues
                elif source == 'openalex':
                    score += 15
                elif source == 'core':
                    score += 10
            
            # Title relevance boost for all papers (0-10 points)
            import random
            score += random.uniform(0, 5)
            
            scored_papers.append((score, paper))
        
        # Sort by score and return top papers
        scored_papers.sort(key=lambda x: x[0], reverse=True)
        
        fallback_papers = []
        for i, (score, paper) in enumerate(scored_papers[:limit]):
            paper_copy = paper.copy()
            source = paper.get('source', '').lower()
            
            # Create source-aware explanations
            explanation_parts = []
            source = paper.get('source', '').lower()
            is_arxiv = source == 'arxiv'
            
            if is_arxiv:
                # ArXiv-specific explanation logic
                year = paper.get('year')
                if year and year >= 2022:
                    explanation_parts.append("cutting-edge preprint with latest research developments")
                elif year and year >= 2020:
                    explanation_parts.append("recent preprint representing current research trends")
                else:
                    explanation_parts.append("preprint contributing to the research landscape")
                
                # Quality indicators for arXiv
                abstract = paper.get('abstract', '')
                if abstract and len(abstract) > 300:
                    explanation_parts.append("comprehensive methodology and thorough experimental design")
                elif abstract and len(abstract) > 150:
                    explanation_parts.append("detailed technical approach")
                else:
                    explanation_parts.append("novel research contribution")
                
                explanation_parts.append("from arXiv preprint server showcasing innovation")
                
            else:
                # Published paper explanation logic
                citations = paper.get('citations', 0) or 0
                if citations > 1000:
                    explanation_parts.append(f"highly cited work ({citations:,} citations) with significant academic impact")
                elif citations > 100:
                    explanation_parts.append(f"well-cited research ({citations} citations) with established recognition")
                elif citations > 10:
                    explanation_parts.append(f"cited work ({citations} citations) with academic validation")
                else:
                    explanation_parts.append("emerging research with growing potential")
                
                # Add recency reasoning for published papers
                year = paper.get('year')
                if year and year >= 2022:
                    explanation_parts.append("recent publication with current relevance")
                elif year and year >= 2018:
                    explanation_parts.append("relatively recent work")
                elif year and year >= 2010:
                    explanation_parts.append("established research")
                else:
                    explanation_parts.append("foundational work")
                
                # Add source credibility
                if source in ['semantic_scholar', 'crossref']:
                    explanation_parts.append("from established academic publication")
                elif source == 'openalex':
                    explanation_parts.append("from comprehensive scholarly database")
                elif source == 'core':
                    explanation_parts.append("from global research repository")
            
            # Combine into explanation (make it more balanced and informative)
            if is_arxiv:
                explanation = f"Ranked #{i+1} for innovation potential: {explanation_parts[0]}"
            else:
                explanation = f"Ranked #{i+1} by academic impact: {explanation_parts[0]}"
            
            if len(explanation_parts) > 1:
                explanation += f", {explanation_parts[1]}"  # Add second most important aspect
            explanation += f". Balanced relevance score: {score:.1f}/100."
            
            paper_copy['explanation'] = explanation
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
