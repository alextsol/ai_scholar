from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from ..services.search_service import SearchService
from ..models.search_request import SearchRequest
from ..models.search_result import SearchResult
from ..models.database import db, SearchHistory
from ..utils.exceptions import ValidationError
from ..utils.error_handler import handle_api_error
import logging

logger = logging.getLogger(__name__)

class SearchController:
    
    def __init__(self, search_service: SearchService):
        self.search_service = search_service
        self.blueprint = Blueprint('search', __name__, url_prefix='/search')
        self._register_routes()
    
    def _register_routes(self):
        self.blueprint.add_url_rule('/api', 'api_search', self.api_search, methods=['POST'])
        self.blueprint.add_url_rule('/history', 'search_history', self.get_search_history, methods=['GET'])
        self.blueprint.add_url_rule('/history/<int:search_id>', 'get_search_details', self.get_search_details, methods=['GET'])
    
    @login_required
    @handle_api_error
    def api_search(self):
        data = request.get_json()
        if not data:
            raise ValidationError("No data provided", user_message="Please provide search parameters.")
        
        query = data.get('query', '').strip()
        if not query:
            raise ValidationError("Query is required", user_message="Please enter a search query.")
        
        if len(query) < 3:
            raise ValidationError("Query too short", user_message="Search query must be at least 3 characters long.")
        
        search_request = SearchRequest(
            query=query,
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
    
    @login_required
    def get_search_history(self):
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            
            searches = db.session.query(SearchHistory).filter_by(user_id=current_user.id)\
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
        try:
            search = db.session.query(SearchHistory).filter_by(
                id=search_id, 
                user_id=current_user.id
            ).first()
            
            if not search:
                return jsonify({'error': 'Search not found'}), 404
            
            return jsonify(search.to_dict())
            
        except Exception as e:
            return jsonify({'error': f'Failed to get search details: {str(e)}'}), 500
    
    def _save_search_history(self, search_request: SearchRequest, search_result: SearchResult):
        try:
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
