from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from typing import Optional
from ..services.paper_service import PaperService
from ..services.ai_service import AIService
from ..models.search_result import SearchResult
from ..models.database import db, SearchHistory

class PaperController:
    
    def __init__(self, paper_service: PaperService, ai_service: AIService):
        self.paper_service = paper_service
        self.ai_service = ai_service
        self.blueprint = Blueprint('papers', __name__, url_prefix='/papers')
        self._register_routes()
    
    def _register_routes(self):
        self.blueprint.add_url_rule('/aggregate', 'aggregate_papers', self.aggregate_papers, methods=['POST'])
        self.blueprint.add_url_rule('/rank', 'rank_papers', self.rank_papers, methods=['POST'])
        self.blueprint.add_url_rule('/<paper_id>/details', 'get_paper_details', self.get_paper_details, methods=['GET'])
        self.blueprint.add_url_rule('/compare', 'compare_papers', self.compare_papers, methods=['POST'])
    
    @login_required
    def aggregate_papers(self):
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            query = data.get('query', '')
            limit = data.get('limit', 100)
            ai_result_limit = data.get('ai_result_limit', 10)
            ranking_mode = data.get('ranking_mode', 'ai')
            min_year = data.get('min_year')
            max_year = data.get('max_year')
            
            if not query.strip():
                return jsonify({'error': 'Query is required'}), 400
            
            aggregated_result = self.paper_service.aggregate_and_rank_papers(
                query=query,
                limit=limit,
                ai_result_limit=ai_result_limit,
                ranking_mode=ranking_mode,
                min_year=min_year,
                max_year=max_year
            )
            
            self._save_aggregation_history(
                query, limit, ai_result_limit, ranking_mode, 
                min_year, max_year, aggregated_result
            )
            
            return jsonify({
                'success': True,
                'results': aggregated_result.papers,
                'total_count': aggregated_result.total_found,
                'sources_used': aggregated_result.backends_used,
                'ranking_applied': aggregated_result.ranking_mode,
                'search_time': aggregated_result.processing_time
            })
            
        except Exception as e:
            return jsonify({'error': f'Aggregation failed: {str(e)}'}), 500
    
    @login_required
    def rank_papers(self):
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            papers = data.get('papers', [])
            query = data.get('query', '')
            ranking_mode = data.get('ranking_mode', 'ai')
            limit = data.get('limit', 10)
            
            if not papers:
                return jsonify({'error': 'Papers list is required'}), 400
            
            if not query.strip():
                return jsonify({'error': 'Query is required for ranking'}), 400
            
            ranked_papers = self.ai_service.rank_papers(
                query=query,
                papers=papers,
                ranking_mode=ranking_mode,
                limit=limit
            )
            
            return jsonify({
                'success': True,
                'ranked_papers': ranked_papers,
                'ranking_mode': ranking_mode,
                'total_ranked': len(ranked_papers)
            })
            
        except Exception as e:
            return jsonify({'error': f'Ranking failed: {str(e)}'}), 500
    
    @login_required
    def get_paper_details(self, paper_id: str):
        try:
            paper_details = self.paper_service.get_paper_details(paper_id)
            
            if not paper_details:
                return jsonify({'error': 'Paper not found'}), 404
            
            return jsonify({
                'success': True,
                'paper': paper_details
            })
            
        except Exception as e:
            return jsonify({'error': f'Failed to get paper details: {str(e)}'}), 500
    
    @login_required
    def compare_papers(self):
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            papers = data.get('papers', [])
            comparison_criteria = data.get('criteria', ['citations', 'year', 'relevance'])
            
            if len(papers) < 2:
                return jsonify({'error': 'At least 2 papers required for comparison'}), 400
            
            comparison_result = self.paper_service.compare_papers(
                papers=papers,
                criteria=comparison_criteria
            )
            
            return jsonify({
                'success': True,
                'comparison': comparison_result,
                'criteria_used': comparison_criteria
            })
            
        except Exception as e:
            return jsonify({'error': f'Comparison failed: {str(e)}'}), 500
    
    def _save_aggregation_history(self, query: str, limit: int, ai_result_limit: int, 
                                ranking_mode: str, min_year: Optional[int], 
                                max_year: Optional[int], result: SearchResult):
        try:
            search_params = {
                'limit': limit,
                'ai_result_limit': ai_result_limit,
                'ranking_mode': ranking_mode,
                'min_year': min_year,
                'max_year': max_year
            }
            
            search_record = SearchHistory(
                user_id=current_user.id,
                query=query,
                backend='aggregate',
                mode='aggregate',
                search_params=str(search_params),
                results_count=result.total_found
            )
            
            db.session.add(search_record)
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
