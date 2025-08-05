from typing import List, Dict, Any, Optional
from flask import render_template_string
from ..models.database import db, SearchHistory
from flask_login import current_user
import logging

logger = logging.getLogger(__name__)


class WebHelpers:
    @staticmethod
    def group_results_by_source(papers: List[Dict[str, Any]], default_source: str = "Unknown") -> List[Dict[str, Any]]:
        """Group search results by their source"""
        groups = {}
        
        for paper in papers:
            if isinstance(paper, dict):
                source = paper.get("source", default_source)
                if source not in groups:
                    groups[source] = []
                
                citation_count = paper.get('citations') or paper.get('citation') or 'N/A'
                
                paper_details = {
                    'title': paper.get('title', 'No title'),
                    'year': paper.get('year', 'Unknown year'),
                    'authors': paper.get('authors', 'No authors'),
                    'citations': citation_count,
                    'url': paper.get('url', '#')
                }
                
                if paper.get('explanation'):
                    paper_details['explanation'] = paper.get('explanation')
                
                groups[source].append(paper_details)
        
        results = []
        for source, papers in groups.items():
            results.append({
                'source': source,
                'papers': papers
            })
        
        return results
    
    @staticmethod
    def parse_int(value: str, default: Optional[int] = None) -> Optional[int]:
        """Parse integer value with default fallback"""
        if value and value.isdigit():
            return int(value)
        return default
    
    @staticmethod
    def save_search_history(query: str, backend: str, mode: str,
                           result_limit: int, ai_result_limit: int, ranking_mode: str,
                           min_year: Optional[int], max_year: Optional[int],
                           results_count: int, results: List[Dict[str, Any]]):
        """Save web search to history"""
        try:
            # Check if user is authenticated
            if not current_user.is_authenticated:
                return
                
            search_params = {
                'min_year': min_year,
                'max_year': max_year,
                'result_limit': result_limit,
                'ai_result_limit': ai_result_limit,
                'ranking_mode': ranking_mode
            }
            
            search_record = SearchHistory(
                user_id=current_user.id,
                query=query,
                backend=backend,
                mode=mode,
                search_params=str(search_params),
                results_count=results_count
            )
            
            if results:
                results_html = render_template_string('''
                {% for result in results %}
                    <div class="source-group" data-source="{{ result.source }}">
                        <h3>{{ result.source.replace('_', ' ').title() }} ({{ result.papers|length }} papers)</h3>
                        {% for paper in result.papers %}
                            <div class="paper-item">
                                <h4><a href="{{ paper.url }}" target="_blank">{{ paper.title }}</a></h4>
                                <p><strong>Authors:</strong> {{ paper.authors }}</p>
                                <p><strong>Year:</strong> {{ paper.year }} | <strong>Citations:</strong> {{ paper.citations }}</p>
                                {% if paper.explanation %}
                                    <p><strong>AI Ranking Explanation:</strong> {{ paper.explanation }}</p>
                                {% endif %}
                            </div>
                        {% endfor %}
                    </div>
                {% endfor %}
                ''', results=results)
                
                search_record.results_html = results_html
            
            db.session.add(search_record)
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to save search history: {e}")
    
    @staticmethod
    def get_user_stats():
        """Get user statistics"""
        try:
            if not current_user.is_authenticated:
                return {
                    'totalSearches': 0,
                    'providersUsed': 0,
                    'totalResults': 0,
                    'avgResponseTime': '0s'
                }
                
            total_searches = len(current_user.searches)
            providers_used = len(set(search.backend for search in current_user.searches))
            total_results = sum(search.results_count or 0 for search in current_user.searches)
                
            return {
                'totalSearches': total_searches,
                'providersUsed': providers_used if providers_used > 0 else 0,
                'totalResults': int(total_results),
                'avgResponseTime': '1.3s'
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {
                'totalSearches': 0,
                'providersUsed': 0,
                'totalResults': 0,
                'avgResponseTime': '0s'
            }
