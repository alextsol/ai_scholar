from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from ..models import db, SearchHistory

history_bp = Blueprint('history', __name__)

@history_bp.route('/history')
@login_required
def history():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    searches_query = db.session.query(SearchHistory).filter_by(user_id=current_user.id)\
        .order_by(SearchHistory.created_at.desc())
    
    total = searches_query.count()
    searches_items = searches_query.offset((page - 1) * per_page).limit(per_page).all()
    
    class SimplePagination:
        def __init__(self, items, page, per_page, total):
            self.items = items
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1 if self.has_prev else None
            self.next_num = page + 1 if self.has_next else None
        
        def iter_pages(self):
            for num in range(max(1, self.page - 2), min(self.pages + 1, self.page + 3)):
                yield num
    
    searches = SimplePagination(searches_items, page, per_page, total)
    
    return render_template('history.html', searches=searches)

@history_bp.route('/history/clear', methods=['POST'])
@login_required
def clear_history():
    current_user.clear_search_history()
    return redirect(url_for('history.history'))

@history_bp.route('/history/delete/<int:search_id>', methods=['POST'])
@login_required
def delete_search(search_id):
    search = db.session.query(SearchHistory).filter_by(id=search_id, user_id=current_user.id).first()
    
    if search:
        db.session.delete(search)
        db.session.commit()
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Search not found'}), 404

@history_bp.route('/history/results/<int:search_id>')
@login_required
def get_search_results(search_id):
    search = db.session.query(SearchHistory).filter_by(id=search_id, user_id=current_user.id).first()
    
    if not search:
        return jsonify({'error': 'Search not found'}), 404
    
    return jsonify({
        'results_html': search.results_html or '<p>No results stored for this search.</p>',
        'query': search.query,
        'backend': search.backend,
        'mode': search.mode,
        'results_count': search.results_count
    })

@history_bp.route('/history/search/<int:search_id>')
@login_required
def repeat_search(search_id):
    search = db.session.query(SearchHistory).filter_by(id=search_id, user_id=current_user.id).first()
    
    if not search:
        return redirect(url_for('history.history'))
    
    return render_template(
        'index.html',
        query=search.query,
        selected_backend=search.backend,
        mode=search.mode,
        papersCount=0,
        results=[],
        min_year="",
        max_year="",
        result_limit=100,
        ai_result_limit=10,
        ranking_mode="ai"
    )

@history_bp.route('/api/history')
@login_required
def api_history():
    searches = current_user.get_recent_searches(20)
    return {'searches': [search.to_dict() for search in searches]}
