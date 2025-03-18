import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, session, redirect, url_for
from paper_search import search_papers
from paper_aggregator import aggregate_and_rank_papers, check_bias_in_aggregated_papers
from analytics import log_search
import json

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24))

def group_results_by_source(papers, default_source="Unknown"):
    groups = {}
    for paper in papers:
        if isinstance(paper, dict):
            src = paper.get("source", default_source)
            groups.setdefault(src, []).append(paper)
    return groups

@app.route('/', methods=['GET', 'POST'])
def index():
    bias_report = None
    chatbot_response = ""
    last_search = None

    if request.method == 'POST':
        user_input = request.form['query']
        mode = request.form.get('mode')
        backend = request.form.get('backend')
        ip_address = request.remote_addr

        log_search(user_input, ip_address)

        if mode == "aggregate":
            papers = aggregate_and_rank_papers(user_input)
        else:
            papers = search_papers(user_input, backend=backend)

        # Compute bias report using your helper function
        bias_report = check_bias_in_aggregated_papers(papers)
        
        # Save the complete last search in the session
        last_search = {
            "query": user_input,
            "results": papers
        }
        session['last_search'] = last_search

        # Build your chatbot response (grouping by source, etc.)
        # ... your code to build chatbot_response ...

        return render_template(
            'index.html',
            query="",
            chatbot_response=chatbot_response,
            selected_backend=backend,
            last_search=last_search,
            bias_report=json.dumps(bias_report, indent=2) if bias_report else None
        )
    else:
        last_search = session.get('last_search', None)
        return render_template(
            'index.html',
            query="",
            chatbot_response="",
            selected_backend="",
            last_search=last_search,
            bias_report=None
        )

@app.route('/last_search', methods=['GET'])
def last_search_page():
    last_search = session.get('last_search', None)
    if not last_search:
        return "No previous search found.", 404
    grouped_results = group_results_by_source(last_search.get("results", []))
    return render_template('last_search.html', last_search=last_search, grouped_results=grouped_results)


if __name__ == '__main__':
    app.run(debug=True)
