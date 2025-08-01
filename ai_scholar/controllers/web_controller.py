from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user, login_required
from typing import Optional, Dict, Any, List
from ..services.search_service import SearchService
from ..services.paper_service import PaperService
from ..models.search_request import SearchRequest
from ..models.database import db, SearchHistory

class WebController:
    """Controller handling web UI requests (traditional MVC views)"""
    
    def __init__(self, search_service: SearchService, paper_service: PaperService):
        self.search_service = search_service
        self.paper_service = paper_service
        self.blueprint = Blueprint('web_main', __name__)
        self._register_routes()
    
    def _register_routes(self):
        """Register all web UI routes"""
        self.blueprint.add_url_rule('/', 'index', self.index, methods=['GET', 'POST'])
        self.blueprint.add_url_rule('/results', 'results', self.results, methods=['GET'])
        self.blueprint.add_url_rule('/history', 'history', self.history, methods=['GET'])
        self.blueprint.add_url_rule('/search', 'search_page', self.search_page, methods=['GET', 'POST'])
    
    def index(self):
        """Main search interface"""
        context = {
            'query': '',
            'selected_backend': '',
            'mode': '',
            'min_year': '',
            'max_year': '',
            'result_limit': 100,
            'ai_result_limit': 10,
            'ranking_mode': 'ai',
            'results': [],
            'papersCount': 0,
            'recent_searches': []
        }
        
        if request.method == 'POST':
            try:
                query = request.form.get('query', '').strip()
                mode = request.form.get('mode', '')
                selected_backend = request.form.get('backend', '')
                min_year = self._parse_int(request.form.get('min_year'))
                max_year = self._parse_int(request.form.get('max_year'))
                result_limit = self._parse_int(request.form.get('result_limit'), default=100)
                ai_result_limit = self._parse_int(request.form.get('ai_result_limit'), default=10)
                ranking_mode = request.form.get('ranking_mode', 'ai')
                
                context.update({
                    'query': query,
                    'selected_backend': selected_backend,
                    'mode': mode,
                    'min_year': min_year,
                    'max_year': max_year,
                    'result_limit': result_limit,
                    'ai_result_limit': ai_result_limit,
                    'ranking_mode': ranking_mode
                })
                
                if not query:
                    flash('Please enter a search query', 'error')
                    return render_template('index.html', **context)
                
                if mode == "aggregate":
                    search_result = self.paper_service.aggregate_and_rank_papers(
                        query=query,
                        limit=result_limit,
                        ai_result_limit=ai_result_limit,
                        ranking_mode=ranking_mode,
                        min_year=min_year,
                        max_year=max_year
                    )
                else:
                    search_request = SearchRequest(
                        query=query,
                        backend=selected_backend,
                        limit=result_limit,
                        min_year=min_year,
                        max_year=max_year
                    )
                    search_result = self.search_service.search_papers(search_request)
                
                if search_result and search_result.papers:
                    results = self._group_results_by_source(
                        search_result.papers, 
                        default_source=selected_backend or search_result.backend_used or "Unknown"
                    )
                    context['results'] = results
                    context['papersCount'] = len(search_result.papers)
                    
                    self._save_web_search_history(
                        query, selected_backend or mode, mode, 
                        result_limit, ai_result_limit, ranking_mode,
                        min_year, max_year, len(search_result.papers),
                        results
                    )
                else:
                    flash('No results found for your query', 'info')
                    
            except Exception as e:
                flash(f'Search failed: {str(e)}', 'error')
        
        return render_template('index.html', **context)
    
    def results(self):
        """Display search results (for AJAX requests)"""
        return jsonify({'message': 'Results endpoint'})
    
    @login_required
    def history(self):
        """Display user's search history"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = 20
            
            searches = SearchHistory.query.filter_by(user_id=current_user.id)\
                                        .order_by(SearchHistory.created_at.desc())\
                                        .paginate(page=page, per_page=per_page, error_out=False)
            
            return render_template('history.html', searches=searches)
            
        except Exception as e:
            flash(f'Failed to load search history: {str(e)}', 'error')
            return redirect(url_for('web_main.index'))
    
    def search_page(self):
        """Dedicated search page with advanced options"""
        if request.method == 'POST':
            return self.index()
        
        context = {
            'query': '',
            'selected_backend': '',
            'mode': '',
            'min_year': '',
            'max_year': '',
            'result_limit': 100,
            'ai_result_limit': 10,
            'ranking_mode': 'ai',
            'results': [],
            'papersCount': 0,
            'recent_searches': [],
            'available_backends': ['arxiv', 'semantic_scholar', 'crossref', 'core'],
            'advanced_mode': True
        }
        
        return render_template('search.html', **context)

    def _group_results_by_source(self, papers: List[Dict[str, Any]], default_source: str = "Unknown") -> List[Dict[str, Any]]:
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
    
    def _parse_int(self, value: str, default: Optional[int] = None) -> Optional[int]:
        """Safely parse integer from form input"""
        if value and value.isdigit():
            return int(value)
        return default
    
    def _save_web_search_history(self, query: str, backend: str, mode: str,
                                result_limit: int, ai_result_limit: int, ranking_mode: str,
                                min_year: Optional[int], max_year: Optional[int],
                                results_count: int, results: List[Dict[str, Any]]):
        """Save web search to history"""
        try:
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
                from flask import render_template_string
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
