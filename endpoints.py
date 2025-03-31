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
    
    if request.method == 'POST':
        query = request.form['query']
        mode = request.form.get('mode') 
        selected_backend = request.form.get('backend')
        ip_address = request.remote_addr

        log_search(query, ip_address)

        if mode == "aggregate":
            papers = aggregate_and_rank_papers(query)
        else:
            papers = search_papers(query, backend=selected_backend)
        
        bias_report = compute_fairness_metrics(papers)
        
        # Group results by source for display
        grouped_results = group_results_by_source(papers, default_source=selected_backend or "Unknown")
        chatbot_response = ""
        for src, group in grouped_results.items():
            chatbot_response += f"<h4>{src} results:</h4><ul>"
            for paper in group:
                chatbot_response += (
                    f"<li><strong>{paper.get('title', 'No title')}</strong> "
                    f"({paper.get('year', 'Unknown year')})<br>"
                    f"Authors: {paper.get('authors', 'No authors')}<br>"
                    f"<a href='{paper.get('url', '#')}' target='_blank'>Read More</a></li><br>"
                )
                if mode == "aggregate" and paper.get('explanation'):
                    chatbot_response += f"<em>{paper['explanation']}</em><br>"
                chatbot_response += "</li><br>"
            chatbot_response += "</ul>"
    
    return render_template(
        'index.html',
        query=query,
        chatbot_response=chatbot_response,
        selected_backend=selected_backend,
        bias_report=json.dumps(bias_report, indent=2) if bias_report else None
    )
