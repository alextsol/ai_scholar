from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
import json
from .paper_search import search_papers
from .paper_aggregator import aggregate_and_rank_papers
from .models import db, SearchHistory

bp = Blueprint('main', __name__)

@bp.route('/landing')
def landing():
    return render_template('landing.html')

def group_results_by_source(papers, default_source="Unknown"):
    groups = {}
    for paper in papers:
        if isinstance(paper, dict):
            src = paper.get("source", default_source)
            groups.setdefault(src, []).append(paper)
    return groups

@bp.route('/', methods=['GET', 'POST'])
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('main.landing'))
    query = ""
    selected_backend = ""
    mode = ""
    min_year = ""
    max_year = ""
    papers = []
    result_limit = 100
    ai_result_limit = 100
    ranking_mode = ""
    results = []
    
    if request.method == 'POST':
        query = request.form['query']
        mode = request.form.get('mode') 
        selected_backend = request.form.get('backend')
        ip_address = request.remote_addr
        
        min_year = request.form.get('min_year')
        max_year = request.form.get('max_year')
        result_limit = request.form.get('result_limit', '100')
        ai_result_limit = request.form.get('ai_result_limit', '10')
        ranking_mode = request.form.get('ranking_mode', 'ai')
        
        min_year = int(min_year) if min_year and min_year.isdigit() else None
        max_year = int(max_year) if max_year and max_year.isdigit() else None
        result_limit = int(result_limit) if result_limit.isdigit() else 100
        ai_result_limit = int(ai_result_limit) if ai_result_limit.isdigit() else 10

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
            backend=selected_backend or mode,
            mode=mode,
            search_params=str(search_params),
            results_count=0
        )

        if mode == "aggregate":
            papers = aggregate_and_rank_papers(query, result_limit, ai_result_limit, ranking_mode, min_year, max_year)
        else:
            papers = search_papers(query, result_limit, backend=selected_backend, min_year=min_year, max_year=max_year)
        
        search_record.results_count = len(papers) if papers else 0
        try:
            db.session.add(search_record)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
        
        if papers:
            grouped_results = group_results_by_source(papers, default_source=selected_backend or "Unknown")
            results = []
            for src, group in grouped_results.items():
                source_results = {"source": src, "papers": []}
                for paper in group:
                    citation_count = paper.get('citations')
                    if citation_count is None:
                        citation_count = paper.get('citation')
                    
                    if citation_count is None:
                        citation_count = 'N/A'
                    
                    paper_details = {
                        'title': paper.get('title', 'No title'),
                        'year': paper.get('year', 'Unknown year'),
                        'authors': paper.get('authors', 'No authors'),
                        'citations': citation_count,
                        'url': paper.get('url', '#')
                    }
                    
                    if mode == "aggregate" and paper.get('explanation'):
                        paper_details['explanation'] = paper.get('explanation')
                    
                    source_results["papers"].append(paper_details)
                results.append(source_results)
        else:
            results = []
    
    recent_searches = current_user.get_recent_searches(10) if current_user.is_authenticated else []
    
    # Render the template
    rendered_template = render_template(
        'index.html',
        query=query,
        papersCount=len(papers),
        results=results,
        selected_backend=selected_backend,
        mode=mode,
        min_year=min_year,
        max_year=max_year,
        result_limit=result_limit,
        ai_result_limit=ai_result_limit,
        ranking_mode=ranking_mode,
        recent_searches=recent_searches
    )
    
    # Store the results HTML if we have results and a search record
    if results and search_record and current_user.is_authenticated:
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
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
    
    return rendered_template

@bp.route('/history')
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

@bp.route('/history/clear', methods=['POST'])
@login_required
def clear_history():
    current_user.clear_search_history()
    return redirect(url_for('main.history'))

@bp.route('/history/delete/<int:search_id>', methods=['POST'])
@login_required
def delete_search(search_id):
    search = db.session.query(SearchHistory).filter_by(id=search_id, user_id=current_user.id).first()
    
    if search:
        db.session.delete(search)
        db.session.commit()
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Search not found'}), 404

@bp.route('/history/results/<int:search_id>')
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

@bp.route('/history/search/<int:search_id>')
@login_required
def repeat_search(search_id):
    search = db.session.query(SearchHistory).filter_by(id=search_id, user_id=current_user.id).first()
    
    if not search:
        return redirect(url_for('main.history'))
    
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

@bp.route('/api/history')
@login_required
def api_history():
    searches = current_user.get_recent_searches(20)
    return {'searches': [search.to_dict() for search in searches]}
