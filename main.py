# main.py
from flask import Flask, render_template, request
from chatbot import generate_chat_response
from paper_search import search_papers
from paper_aggregator import aggregate_and_rank_papers
from analytics import log_search

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        user_input = request.form['query']
        mode = request.form.get('mode')  
        backend = request.form.get('backend') 
        ip_address = request.remote_addr

        log_search(user_input, ip_address)

        if mode == "aggregate":
            papers = aggregate_and_rank_papers(user_input)
            chatbot_response = "<h4>Aggregated & Ranked Results:</h4><ul>"
            for idx, paper in enumerate(papers, 1):
                chatbot_response += (
                    f"<li><strong>{paper['title']}</strong> ({paper['year']})<br>"
                    f"Authors: {paper['authors']}<br>"
                    f"<a href='{paper['url']}' target='_blank'>Read More</a></li><br>"
                )
            chatbot_response += "</ul>"
        else:
            papers = search_papers(user_input, backend=backend)
            chatbot_response = "<h4>Search Results:</h4><ul>"
            for idx, paper in enumerate(papers, 1):
                chatbot_response += (
                    f"<li><strong>{paper['title']}</strong> ({paper['year']})<br>"
                    f"Authors: {paper['authors']}<br>"
                    f"<a href='{paper['url']}' target='_blank'>Read More</a></li><br>"
                )
            chatbot_response += "</ul>"

        return render_template('index.html', query=user_input, chatbot_response=chatbot_response, selected_backend=backend)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
