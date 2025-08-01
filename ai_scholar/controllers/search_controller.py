from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from ..services.search_service import SearchService
from ..models.search_request import SearchRequest
from ..models.search_result import SearchResult
from ..models.database import db, SearchHistory

class SearchController:
    """Controller handling search-related HTTP requests"""
    
    def __init__(self, search_service: SearchService):
        self.search_service = search_service
        self.blueprint = Blueprint('search', __name__, url_prefix='/search')
        self._register_routes()
    
    def _register_routes(self):
        """Register all search-related routes"""
        self.blueprint.add_url_rule('/api', 'api_search', self.api_search, methods=['POST'])
        self.blueprint.add_url_rule('/history', 'search_history', self.get_search_history, methods=['GET'])
        self.blueprint.add_url_rule('/history/<int:search_id>', 'get_search_details', self.get_search_details, methods=['GET'])
    
    @login_required
    def api_search(self):
        """Handle API search requests"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            search_request = SearchRequest(
                query=data.get('query', ''),
                backends=[data.get('backend')] if data.get('backend') else None,
                limit=data.get('limit', 100),
                min_year=data.get('min_year'),
                max_year=data.get('max_year')
            )
            
            # Validation is handled in __post_init__
            search_result = self.search_service.search_papers(search_request)
            self._save_search_history(search_request, search_result)
            
            return jsonify({
                'success': True,
                'results': search_result.papers,
                'total_count': search_result.total_found,
                'backend_used': search_result.backends_used[0] if search_result.backends_used else 'unknown',
                'search_time': search_result.processing_time
            })
            
        except Exception as e:
            return jsonify({'error': f'Search failed: {str(e)}'}), 500
    
    @login_required
    def get_search_history(self):
        """Get user's search history"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            
            searches = SearchHistory.query.filter_by(user_id=current_user.id)\
                                        .order_by(SearchHistory.created_at.desc())\
                                        .paginate(page=page, per_page=per_page, error_out=False)
            
            return jsonify({
                'searches': [search.to_dict() for search in searches.items],
                'total': searches.total,
                'pages': searches.pages,
                'current_page': searches.page
            })
            
        except Exception as e:
            return jsonify({'error': f'Failed to get search history: {str(e)}'}), 500
    
    @login_required
    def get_search_details(self, search_id: int):
        """Get details of a specific search"""
        try:
            search = SearchHistory.query.filter_by(
                id=search_id, 
                user_id=current_user.id
            ).first()
            
            if not search:
                return jsonify({'error': 'Search not found'}), 404
            
            return jsonify(search.to_dict())
            
        except Exception as e:
            return jsonify({'error': f'Failed to get search details: {str(e)}'}), 500
    
    def _save_search_history(self, search_request: SearchRequest, search_result: SearchResult):
        """Save search to history"""
        try:
            # Get the first backend from the list, or 'default'
            backend = (search_request.backends[0] if search_request.backends else 'default')
            
            search_record = SearchHistory(
                user_id=current_user.id,
                query=search_request.query,
                backend=backend,
                mode='search',
                search_params=f"limit:{search_request.limit},backends:{search_request.backends}",
                results_count=search_result.total_found
            )
            
            db.session.add(search_record)
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
