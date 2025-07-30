from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
import json
from .paper_search import search_papers
from .paper_aggregator import aggregate_and_rank_papers
from .fairness import compute_fairness_metrics
from .analytics import log_search
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
    bias_report = None
    chatbot_response = ""
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

        log_search(query, ip_address)
        
        search_record = SearchHistory(
            user_id=current_user.id,
            query=query,
            backend=selected_backend or mode,
            results_count=0
        )

        if mode == "aggregate":
            papers = aggregate_and_rank_papers(query, result_limit, ai_result_limit, ranking_mode, min_year, max_year)
        else:
            papers = search_papers(query, result_limit, backend=selected_backend, min_year=min_year, max_year=max_year)
        
        bias_report = compute_fairness_metrics(papers)
        
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
    
    return render_template(
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
        bias_report=json.dumps(bias_report, indent=2) if bias_report else None
    )
