from typing import List, Dict, Any
from ..enums.search_modes import RankingMode
from ..config.settings import Settings
import logging

logger = logging.getLogger(__name__)

class PaperRankingService:
    CURRENT_YEAR = 2025
    CITATION_NA_VALUE = 'N/A'
    UNKNOWN_YEAR_VALUE = 'Unknown year'
    
    @staticmethod
    def rank_by_citations(papers: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        def get_citations(paper):
            citations = paper.get('citations') or paper.get('citation') or 0
            try:
                return int(citations) if citations != PaperRankingService.CITATION_NA_VALUE else 0
            except (ValueError, TypeError):
                return 0
        
        papers_with_citations = []
        papers_without_citations = []
        
        for paper in papers:
            citations = get_citations(paper)
            if citations > 0:
                papers_with_citations.append(paper)
            else:
                papers_without_citations.append(paper)
        
        sorted_cited_papers = sorted(papers_with_citations, key=get_citations, reverse=True)
        
        if len(sorted_cited_papers) < limit and papers_without_citations:
            remaining_needed = limit - len(sorted_cited_papers)
            sorted_uncited = sorted(papers_without_citations, 
                                  key=lambda p: p.get('year', 0) if str(p.get('year', 0)).isdigit() else 0, 
                                  reverse=True)
            sorted_papers = sorted_cited_papers + sorted_uncited[:remaining_needed]
        else:
            sorted_papers = sorted_cited_papers
        
        for i, paper in enumerate(sorted_papers[:limit]):
            citations = get_citations(paper)
            rank = i + 1
            title = paper.get('title', '')
            authors = paper.get('authors', '')
            year = paper.get('year', '')
            abstract = paper.get('abstract', '')
            
            explanation = PaperRankingService._generate_citation_explanation(
                paper=paper,
                rank=rank,
                citations=citations,
                title=title,
                authors=authors,
                year=year,
                abstract=abstract
            )
            
            paper['explanation'] = explanation
        
        return sorted_papers[:limit]
    
    @staticmethod
    def rank_by_year(papers: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        def get_year(paper):
            year = paper.get('year', 0)
            try:
                return int(year) if year != PaperRankingService.UNKNOWN_YEAR_VALUE else 0
            except (ValueError, TypeError):
                return 0
        
        def calculate_year_relevance_score(paper):
            year = get_year(paper)
            if year <= 0:
                recency_score = 0.0
            else:
                age = PaperRankingService.CURRENT_YEAR - year
                if age <= 1:
                    recency_score = 1.0
                elif age <= 2:
                    recency_score = 0.9
                elif age <= 3:
                    recency_score = 0.8
                elif age <= 5:
                    recency_score = 0.7
                elif age <= 10:
                    recency_score = 0.5
                else:
                    recency_score = 0.2
            
            quality_score = paper.get('_pre_filter_score', 0.5)
            
            citation_bonus = 0.0
            citations = paper.get('citations', 0)
            if citations and citations != PaperRankingService.CITATION_NA_VALUE:
                try:
                    cite_count = int(citations)
                    if year >= 2020:
                        if cite_count > 100:
                            citation_bonus = 0.2
                        elif cite_count > 50:
                            citation_bonus = 0.15
                        elif cite_count > 20:
                            citation_bonus = 0.1
                        elif cite_count > 5:
                            citation_bonus = 0.05
                except:
                    pass
            
            venue_bonus = 0.0
            venue = paper.get('venue', '').lower()
            if any(term in venue for term in ['nature', 'science', 'cell', 'nejm', 'lancet']):
                venue_bonus = 0.15
            elif any(term in venue for term in ['ieee', 'acm', 'springer', 'elsevier']):
                venue_bonus = 0.1
            
            final_score = (recency_score * 0.5) + (quality_score * 0.3) + (citation_bonus * 0.15) + (venue_bonus * 0.05)
            
            paper['_year_score_components'] = {
                'recency': recency_score,
                'quality': quality_score,
                'citation_bonus': citation_bonus,
                'venue_bonus': venue_bonus,
                'final': final_score,
                'year': year
            }
            
            return final_score
        
        for paper in papers:
            paper['_year_relevance_score'] = calculate_year_relevance_score(paper)
        
        sorted_papers = sorted(papers, 
                             key=lambda p: (p.get('_year_relevance_score', 0), get_year(p)), 
                             reverse=True)
        
        for i, paper in enumerate(sorted_papers[:limit]):
            year = get_year(paper)
            rank = i + 1
            title = paper.get('title', '')
            authors = paper.get('authors', '')
            abstract = paper.get('abstract', '')
            score_components = paper.get('_year_score_components', {})
            
            explanation = PaperRankingService._generate_enhanced_year_explanation(
                paper=paper,
                rank=rank,
                year=year,
                title=title,
                authors=authors,
                abstract=abstract,
                score_components=score_components
            )
            
            paper['explanation'] = explanation
        
        return sorted_papers[:limit]
    
    @staticmethod
    def _generate_citation_explanation(paper: Dict[str, Any], rank: int, citations: int,
                                     title: str, authors: str, year: str, abstract: str) -> str:
        content_indicators = []
        
        title_lower = title.lower()
        if any(term in title_lower for term in ['survey', 'review', 'comprehensive']):
            content_indicators.append('comprehensive survey work')
        elif any(term in title_lower for term in ['novel', 'new', 'innovative']):
            content_indicators.append('innovative research')
        elif any(term in title_lower for term in ['deep', 'neural', 'machine learning', 'ai']):
            content_indicators.append('cutting-edge AI research')
        elif any(term in title_lower for term in ['analysis', 'study', 'investigation']):
            content_indicators.append('analytical study')
        
        author_insight = ""
        if authors and ',' in authors:
            author_count = len(authors.split(','))
            if author_count > 5:
                author_insight = f"collaborative work with {author_count} researchers"
            elif author_count > 2:
                author_insight = f"multi-author collaboration"
        
        method_insights = []
        if abstract:
            abstract_lower = abstract.lower()
            if any(term in abstract_lower for term in ['experiment', 'empirical', 'evaluation']):
                method_insights.append('empirical evaluation')
            if any(term in abstract_lower for term in ['dataset', 'data', 'benchmark']):
                method_insights.append('data-driven analysis')
            if any(term in abstract_lower for term in ['algorithm', 'method', 'approach']):
                method_insights.append('methodological contribution')
            if any(term in abstract_lower for term in ['performance', 'accuracy', 'results']):
                method_insights.append('performance validation')
        
        explanation_parts = []
        
        if citations > 0:
            explanation_parts.append(f"Ranked #{rank} with {citations:,} citations")
        else:
            explanation_parts.append(f"Ranked #{rank} (limited citation data available)")
        
        if content_indicators:
            explanation_parts.append(f"as {content_indicators[0]}")
        
        if method_insights:
            if len(method_insights) == 1:
                explanation_parts.append(f"featuring {method_insights[0]}")
            else:
                explanation_parts.append(f"combining {' and '.join(method_insights[:2])}")
        
        if author_insight:
            explanation_parts.append(f"representing {author_insight}")
        
        if year:
            try:
                year_val = int(year)
                age = PaperRankingService.CURRENT_YEAR - year_val
                if age <= 2:
                    explanation_parts.append("with recent impact")
                elif age <= 5:
                    explanation_parts.append("with sustained influence")
                else:
                    explanation_parts.append("with lasting academic impact")
            except:
                pass
        
        if len(explanation_parts) >= 3:
            base_explanation = f"{explanation_parts[0]} {explanation_parts[1]} {explanation_parts[2]}"
            if len(explanation_parts) > 3:
                base_explanation += f", {explanation_parts[3]}"
        else:
            base_explanation = " ".join(explanation_parts)
        
        if citations > 10000:
            impact_note = "indicating exceptional influence in shaping the field"
        elif citations > 5000:
            impact_note = "demonstrating significant scholarly impact"
        elif citations > 1000:
            impact_note = "showing strong academic recognition"
        elif citations > 100:
            impact_note = "reflecting solid scholarly interest"
        elif citations > 0:
            impact_note = "representing emerging academic contribution"
        else:
            if any(term in title_lower for term in ['2024', '2025']) or (year and int(year) >= 2024):
                impact_note = "representing recent contribution with potential for future impact"
            else:
                impact_note = "selected for topical relevance and research quality"
        
        return f"{base_explanation}, {impact_note}."
    
    @staticmethod
    def _generate_enhanced_year_explanation(paper: Dict[str, Any], rank: int, year: int,
                                          title: str, authors: str, abstract: str, 
                                          score_components: Dict[str, Any]) -> str:
        recency_score = score_components.get('recency', 0)
        quality_score = score_components.get('quality', 0)
        citation_bonus = score_components.get('citation_bonus', 0)
        venue_bonus = score_components.get('venue_bonus', 0)
        final_score = score_components.get('final', 0)
        
        primary_factor = ""
        if recency_score >= 0.9 and citation_bonus > 0.1:
            primary_factor = "exceptional recent impact"
        elif recency_score >= 0.9:
            primary_factor = "cutting-edge recency"
        elif citation_bonus > 0.15:
            primary_factor = "high-impact contemporary work"
        elif venue_bonus > 0.1:
            primary_factor = "prestigious venue publication"
        elif quality_score > 0.7:
            primary_factor = "high relevance and quality"
        else:
            primary_factor = "balanced recency and relevance"
        
        content_type = ""
        title_lower = title.lower()
        
        if any(term in title_lower for term in ['survey', 'review', 'comprehensive', 'overview']):
            content_type = "comprehensive survey"
        elif any(term in title_lower for term in ['novel', 'new', 'introducing', 'breakthrough']):
            content_type = "novel research"
        elif any(term in title_lower for term in ['analysis', 'study', 'investigation', 'evaluation']):
            content_type = "analytical study"
        elif any(term in title_lower for term in ['framework', 'method', 'approach', 'algorithm']):
            content_type = "methodological contribution"
        elif any(term in title_lower for term in ['application', 'implementation', 'system']):
            content_type = "practical application"
        else:
            content_type = "research work"
        
        domain_insights = []
        combined_text = f"{title} {abstract}".lower()
        
        if any(term in combined_text for term in ['transformer', 'attention', 'bert', 'gpt', 'llm', 'large language model']):
            domain_insights.append('LLM/Transformers')
        elif any(term in combined_text for term in ['neural network', 'deep learning', 'cnn', 'rnn']):
            domain_insights.append('deep learning')
        elif any(term in combined_text for term in ['machine learning', 'ml', 'artificial intelligence', 'ai']):
            domain_insights.append('AI/ML')
        
        if any(term in combined_text for term in ['computer vision', 'image recognition', 'visual', 'opencv']):
            domain_insights.append('computer vision')
        if any(term in combined_text for term in ['natural language processing', 'nlp', 'text analysis', 'sentiment']):
            domain_insights.append('NLP')
        if any(term in combined_text for term in ['healthcare', 'medical', 'clinical', 'biomedical', 'drug']):
            domain_insights.append('healthcare AI')
        if any(term in combined_text for term in ['robotics', 'autonomous', 'control', 'navigation']):
            domain_insights.append('robotics')
        if any(term in combined_text for term in ['quantum', 'blockchain', 'cryptocurrency', 'web3']):
            domain_insights.append('emerging tech')
        
        age = PaperRankingService.CURRENT_YEAR - year
        if age <= 0:
            temporal_context = "cutting-edge 2025 research"
            impact_timeline = "representing the absolute latest developments"
        elif age == 1:
            temporal_context = "very recent 2024 work"
            impact_timeline = "capturing immediate research trends"
        elif age == 2:
            temporal_context = "recent 2023 contribution"
            impact_timeline = "reflecting current methodological advances"
        elif age <= 3:
            temporal_context = "contemporary research"
            impact_timeline = "providing modern technical perspectives"
        elif age <= 5:
            temporal_context = "established recent work"
            impact_timeline = "offering proven contemporary approaches"
        else:
            temporal_context = "foundational work"
            impact_timeline = "contributing established principles"
        
        explanation_parts = []
        explanation_parts.append(f"Ranked #{rank} for {primary_factor}")
        
        if domain_insights:
            if len(domain_insights) == 1:
                explanation_parts.append(f"as {year} {content_type} in {domain_insights[0]}")
            else:
                explanation_parts.append(f"as {year} {content_type} bridging {' and '.join(domain_insights[:2])}")
        else:
            explanation_parts.append(f"as {year} {content_type}")
        
        ranking_insights = []
        if citation_bonus > 0.15:
            citations = paper.get('citations', 0)
            try:
                cite_count = int(citations)
                ranking_insights.append(f"with {cite_count} citations demonstrating immediate impact")
            except:
                ranking_insights.append("with notable citation impact")
        
        if venue_bonus > 0.1:
            venue = paper.get('venue', '')
            if venue:
                ranking_insights.append(f"published in prestigious {venue}")
            else:
                ranking_insights.append("from high-quality publication venue")
        
        if quality_score > 0.8:
            ranking_insights.append("featuring exceptional topical relevance")
        elif quality_score > 0.6:
            ranking_insights.append("with strong content quality")
        
        base_explanation = " ".join(explanation_parts)
        
        if ranking_insights:
            if len(ranking_insights) == 1:
                base_explanation += f", {ranking_insights[0]}"
            else:
                base_explanation += f", {ranking_insights[0]} and {ranking_insights[1]}"
        
        value_proposition = f"This {temporal_context} is essential for {impact_timeline} in the field"
        
        if final_score > 0.9:
            recommendation = "representing must-read contemporary research"
        elif final_score > 0.8:
            recommendation = "offering valuable recent insights"
        elif final_score > 0.7:
            recommendation = "providing relevant current perspectives"
        else:
            recommendation = "contributing to the current research landscape"
        
        return f"{base_explanation}. {value_proposition}, {recommendation}."
