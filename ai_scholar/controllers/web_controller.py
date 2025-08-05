from flask import Blueprint, render_template, request, flash
from flask_login import current_user, login_required
from ..services.search_service import SearchService
from ..services.paper_service import PaperService
from ..models.search_request import SearchRequest
from ..utils.exceptions import AIScholarError, RateLimitError
from ..utils.error_handler import ErrorHandler
from ..utils.web_helpers import WebHelpers
from ..enums import SearchMode
import logging

logger = logging.getLogger(__name__)

class WebController:
    
    def __init__(self, search_service: SearchService, paper_service: PaperService):
        self.search_service = search_service
        self.paper_service = paper_service
        self.blueprint = Blueprint('web_main', __name__)
        self._register_routes()
    
    def _register_routes(self):
        """Register all web UI routes"""
        self.blueprint.add_url_rule('/', 'index', login_required(self.index), methods=['GET', 'POST'])
        self.blueprint.add_url_rule('/search', 'search_page', login_required(self.search_page), methods=['GET', 'POST'])
    
    def index(self):
        """Main search interface"""
        recent_searches = []
        if current_user.is_authenticated:
            try:
                recent_searches = current_user.get_recent_searches(limit=10)
            except Exception as e:
                pass
        
        query_param = request.args.get('query', '').strip()
        backend_param = request.args.get('backend', 'crossref')
        mode_param = request.args.get('mode', '')
        
        context = {
            'query': query_param,
            'selected_backend': backend_param,
            'mode': mode_param,
            'min_year': '',
            'max_year': '',
            'result_limit': 50,
            'ai_result_limit': 50,
            'ranking_mode': 'ai',
            'results': [],
            'papersCount': 0,
            'recent_searches': recent_searches
        }
        
        if request.method == 'POST':
            try:
                query = request.form.get('query', '').strip()
                mode = request.form.get('mode', '')
                selected_backend = request.form.get('backend', '')
                min_year = WebHelpers.parse_int(request.form.get('min_year'))
                max_year = WebHelpers.parse_int(request.form.get('max_year'))
                result_limit = WebHelpers.parse_int(request.form.get('result_limit'), default=50)
                ai_result_limit = WebHelpers.parse_int(request.form.get('ai_result_limit'), default=50)
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
                
                if mode == SearchMode.AGGREGATE.value:
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
                        backends=[selected_backend] if selected_backend else None,
                        limit=result_limit,
                        min_year=min_year,
                        max_year=max_year
                    )
                    search_result = self.search_service.search_papers(search_request)
                
                # Always save search history regardless of results
                results_count = len(search_result.papers) if search_result and search_result.papers else 0
                results_for_history = []
                
                if search_result and search_result.papers:
                    backend_used = (search_result.backends_used[0] if search_result.backends_used else "Unknown")
                    
                    # Convert Paper objects to dictionaries for UI display
                    papers_as_dicts = []
                    for paper in search_result.papers:
                        if hasattr(paper, 'to_dict'):
                            papers_as_dicts.append(paper.to_dict())
                        elif isinstance(paper, dict):
                            papers_as_dicts.append(paper)
                        else:
                            # Fallback for unknown paper types
                            papers_as_dicts.append({
                                'title': getattr(paper, 'title', 'No title'),
                                'authors': getattr(paper, 'authors', 'No authors'),
                                'year': getattr(paper, 'year', None),
                                'url': getattr(paper, 'url', '#'),
                                'citations': getattr(paper, 'citations', None),
                                'source': getattr(paper, 'source', backend_used),
                                'explanation': getattr(paper, 'explanation', None)
                            })
                    
                    results = WebHelpers.group_results_by_source(
                        papers_as_dicts, 
                        default_source=selected_backend or backend_used
                    )
                    
                    context['results'] = results
                    context['papersCount'] = len(search_result.papers)
                    results_for_history = results
                    
                    # Add aggregation statistics if available
                    if hasattr(search_result, 'aggregation_stats') and search_result.aggregation_stats:
                        context['aggregation_stats'] = search_result.aggregation_stats
                else:
                    flash('No results found for your query', 'info')
                    backend_used = selected_backend or 'Unknown'
                
                # Save search history (moved outside the results check)
                WebHelpers.save_search_history(
                    query, selected_backend or mode, mode, 
                    result_limit, ai_result_limit, ranking_mode,
                    min_year, max_year, results_count,
                    results_for_history
                )
                    
            except AIScholarError as e:
                ErrorHandler.log_error(e, "web_search", str(current_user.id) if current_user.is_authenticated else None)
                flash(e.user_message, 'error')
                
                # For rate limit errors, provide more specific guidance
                if isinstance(e, RateLimitError):
                    retry_time = e.retry_after_seconds
                    if retry_time and retry_time < 300:  # Less than 5 minutes
                        time_str = f"{retry_time} seconds" if retry_time < 60 else f"{retry_time // 60} minutes"
                        flash(f"Please wait {time_str} before searching again.", 'info')
                
            except Exception as e:
                # Handle unexpected errors
                ErrorHandler.log_error(e, "web_search", str(current_user.id) if current_user.is_authenticated else None)
                flash('An unexpected error occurred. Please try again later.', 'error')
        
        return render_template('index.html', **context)
    
    def search_page(self):
        if request.method == 'POST':
            return self.index()
        
        # Get recent searches for authenticated user
        recent_searches = []
        if current_user.is_authenticated:
            try:
                recent_searches = current_user.get_recent_searches(limit=10)
            except Exception as e:
                pass
        
        # Get URL parameters for pre-filling form (e.g., from repeat search)
        query_param = request.args.get('query', '')
        backend_param = request.args.get('backend', 'crossref')
        mode_param = request.args.get('mode', '')
        
        context = {
            'query': query_param,
            'selected_backend': backend_param,
            'mode': mode_param,
            'min_year': '',
            'max_year': '',
            'result_limit': 50,
            'ai_result_limit': 50,
            'ranking_mode': 'ai',
            'results': [],
            'papersCount': 0,
            'recent_searches': recent_searches,
            'available_backends': ['crossref', 'arxiv', 'semantic_scholar', 'core'],
            'advanced_mode': True
        }
        
        return render_template('search.html', **context)
