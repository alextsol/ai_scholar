from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user, login_required
from ..models.database import db, SearchHistory
import logging

logger = logging.getLogger(__name__)


class HistoryController:
    """Controller for managing search history"""
    
    def __init__(self):
        self.blueprint = Blueprint('history', __name__)
        self._register_routes()
    
    def _register_routes(self):
        """Register all history routes"""
        self.blueprint.add_url_rule('/history', 'history', login_required(self.history), methods=['GET'])
        
        # History API endpoints for sidebar functionality
        self.blueprint.add_url_rule('/history/delete/<int:search_id>', 'history_delete', 
                                   login_required(self.delete_history_item), methods=['POST'])
        self.blueprint.add_url_rule('/history/clear', 'history_clear_api', 
                                   login_required(self.clear_history_api), methods=['POST'])
        
        # User stats API
        self.blueprint.add_url_rule('/api/user-stats', 'user_stats', 
                                   login_required(self.user_stats), methods=['GET'])

    def history(self):
        try:
            page = request.args.get('page', 1, type=int)
            per_page = 20
            
            searches = db.session.query(SearchHistory).filter_by(
                user_id=current_user.id
            ).order_by(SearchHistory.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return render_template('history.html', searches=searches)
            
        except Exception as e:
            logger.error(f"Error loading search history: {e}")
            flash('Error loading search history', 'error')
            return redirect(url_for('web_main.index'))

    def delete_history_item(self, search_id: int):
        try:
            search_record = db.session.query(SearchHistory).filter_by(
                id=search_id, 
                user_id=current_user.id
            ).first()
            
            if not search_record:
                return jsonify({'success': False, 'error': 'Search not found'}), 404
            
            db.session.delete(search_record)
            db.session.commit()
            
            return jsonify({'success': True})
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting history item {search_id}: {e}")
            return jsonify({'success': False, 'error': 'Failed to delete search'}), 500

    def clear_history_api(self):
        try:
            db.session.query(SearchHistory).filter_by(user_id=current_user.id).delete()
            db.session.commit()
            return jsonify({'success': True})
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error clearing history: {e}")
            return jsonify({'success': False, 'error': 'Failed to clear history'}), 500

    def user_stats(self):
        try:
            from ..utils.web_helpers import WebHelpers
            stats = WebHelpers.get_user_stats()
            return jsonify(stats)
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return jsonify({
                'totalSearches': 0,
                'providersUsed': 0,
                'totalResults': 0,
                'avgResponseTime': '0s'
            }), 200
