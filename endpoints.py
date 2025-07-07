from flask import Blueprint, render_template, request
import json
from paper_search import search_papers
from paper_aggregator import aggregate_and_rank_papers
from fairness import compute_fairness_metrics
from analytics import log_search

bp = Blueprint('main', __name__)

def group_results_by_source(papers, default_source="Unknown"):
    groups = {}
    for paper in papers:
        if isinstance(paper, dict):
            src = paper.get("source", default_source)
            groups.setdefault(src, []).append(paper)
    return groups

@bp.route('/', methods=['GET', 'POST'])
def index():
    bias_report = None
    chatbot_response = ""
    query = ""
    selected_backend = ""
    mode =""
    min_year =""
    max_year =""
    papers=[]
    result_limit = 100
    ai_result_limit = 100
    ranking_mode =""
    
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
        
        try:
            min_year = int(min_year) if min_year else None
        except ValueError:
            min_year = None
        try:
            max_year = int(max_year) if max_year else None
        except ValueError:
            max_year = None
            
        try:
            result_limit = int(result_limit)
        except ValueError:
            result_limit = 100
            
        try:
            ai_result_limit = int(ai_result_limit)
        except ValueError:
            ai_result_limit = 10

        log_search(query, ip_address)

        if mode == "aggregate":
            papers = aggregate_and_rank_papers(query,result_limit,ai_result_limit,ranking_mode,min_year=min_year, max_year=max_year)
        else:
            papers = search_papers(query,result_limit, backend=selected_backend, min_year=min_year, max_year=max_year)
        
        bias_report = compute_fairness_metrics(papers)
        
        if papers:
            grouped_results = group_results_by_source(papers, default_source=selected_backend or "Unknown")
            chatbot_response = ""
            for src, group in grouped_results.items():
                chatbot_response += f"<h4>{src} results:</h4><ul>"
                for paper in group:
                    chatbot_response += (
                        f"<li><strong>{paper.get('title', 'No title')}</strong> "
                        f"({paper.get('year', 'Unknown year')})<br>"
                        f"<strong>Authors</strong>: {paper.get('authors', 'No authors')}<br>"
                        f"<strong>Citations</strong>: {paper.get('citation', 'N/A')}<br>"
                        f"<a href='{paper.get('url', '#')}' target='_blank'>Read More</a></li></br>"
                    )
                    if mode == "aggregate" and paper.get('explanation'):
                        chatbot_response += f"<em>{paper['explanation']}</em><br>"
                    chatbot_response += "</li><br>"
                chatbot_response += "</ul>"
    
    return render_template(
        'index.html',
        query=query,
        papersCount = len(papers),
        chatbot_response=chatbot_response,
        selected_backend=selected_backend,
        mode=mode,
        min_year=min_year,
        max_year=max_year,
        result_limit=result_limit,
        ai_result_limit=ai_result_limit,
        ranking_mode=ranking_mode,
        bias_report=json.dumps(bias_report, indent=2) if bias_report else None
    )
