from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from ..config.settings import Settings

class AdminController:
    
    def __init__(self):
        self.blueprint = Blueprint('admin', __name__, url_prefix='/admin')
        self._register_routes()
    
    def _register_routes(self):
        self.blueprint.add_url_rule('/', 'dashboard', login_required(self.dashboard), methods=['GET'])
        self.blueprint.add_url_rule('/optimization', 'optimization', login_required(self.optimization_settings), methods=['GET', 'POST'])
        self.blueprint.add_url_rule('/stats', 'stats', login_required(self.aggregation_stats), methods=['GET'])
    
    def dashboard(self):
        """Admin dashboard"""
        # Simple admin check - you might want to implement proper role-based access
        if not current_user.is_authenticated:
            flash('Access denied', 'error')
            return redirect(url_for('web_main.index'))
        
        return render_template('admin/dashboard.html')
    
    def optimization_settings(self):
        """Manage optimization settings"""
        if request.method == 'POST':
            try:
                # Update settings (in a real app, you'd want to persist these)
                new_max_papers = request.form.get('max_papers_for_ai', type=int)
                new_max_per_provider = request.form.get('max_per_provider', type=int)
                new_min_score = request.form.get('pre_filter_min_score', type=float)
                
                if new_max_papers and 50 <= new_max_papers <= 500:
                    Settings.MAX_PAPERS_FOR_AI = new_max_papers
                    
                if new_max_per_provider and 10 <= new_max_per_provider <= 200:
                    Settings.MAX_PER_PROVIDER = new_max_per_provider
                    
                if new_min_score and 0.1 <= new_min_score <= 0.9:
                    Settings.PRE_FILTER_MIN_SCORE = new_min_score
                
                flash('Settings updated successfully', 'success')
                
            except Exception as e:
                flash(f'Error updating settings: {str(e)}', 'error')
        
        current_settings = {
            'MAX_PAPERS_FOR_AI': Settings.MAX_PAPERS_FOR_AI,
            'MAX_PER_PROVIDER': Settings.MAX_PER_PROVIDER,
            'MAX_PER_PROVIDER_AFTER_FILTER': Settings.MAX_PER_PROVIDER_AFTER_FILTER,
            'PRE_FILTER_MIN_SCORE': Settings.PRE_FILTER_MIN_SCORE
        }
        
        return render_template('admin/optimization.html', settings=current_settings)
    
    def aggregation_stats(self):
        """API endpoint for aggregation statistics"""
        # This would return recent aggregation statistics
        # For now, return current settings
        return jsonify({
            'current_settings': {
                'max_papers_for_ai': Settings.MAX_PAPERS_FOR_AI,
                'max_per_provider': Settings.MAX_PER_PROVIDER,
                'pre_filter_min_score': Settings.PRE_FILTER_MIN_SCORE
            },
            'recommendations': {
                'status': 'optimal',
                'message': 'Current settings are within recommended ranges'
            }
        })
