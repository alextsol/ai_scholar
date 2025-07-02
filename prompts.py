def ai_ranking(query, ai_result_limit, papers_json):
    return (
        f"Based on the query '{query}', review the following list of paper titles and authors, and select the top {ai_result_limit} most relevant papers. "
        "For each selected paper, provide a brief explanation of its relevance. "
        "Return your answer as a JSON array of objects with the keys 'title', 'authors', and 'explanation'.\n\n"
        f"Papers:\n{papers_json}"
    )
    
def citation_ranking(query, ai_result_limit, papers_json):
    return (
        f"Based on the query '{query}', review the following list of paper titles =t, authors =a, citations =c. "
        "If any paper have citation:'Not availdable' Search for their citation count in the web and include them in the ranking."
        f"Rank all papers by the number of citations in descending order and select the top {ai_result_limit} papers."
        "For each selected paper, always include the citation count and provide a brief explanation of its relevance."
        "Return your answer as a JSON array of objects with the keys 'title', 'authors', 'citations', and 'explanation'.\n\n"
        f"Papers:\n{papers_json}"
    )