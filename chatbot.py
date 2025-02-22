from paper_search import search_papers

def generate_chat_response(user_input, backend=None):
    if user_input.lower().startswith("search papers on"):
        query = user_input.replace("search papers on", "").strip()
        papers = search_papers(query, backend=backend)
        if isinstance(papers, str):
            return papers
        response = "<h4>Search Results:</h4><ul>"
        for idx, paper in enumerate(papers, 1):
            response += (
                f"<li><strong>{paper['title']}</strong> ({paper['year']})<br>"
                f"Authors: {paper['authors']}<br>"
                f"<a href='{paper['url']}' target='_blank'>Read More</a></li><br>"
            )
        response += "</ul>"
        return response
    else:
        return "Please use 'search papers on <your query>' to search for papers."
