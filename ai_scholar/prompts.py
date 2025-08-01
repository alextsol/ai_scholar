def ai_ranking_prompt(query, batch_size, papers_json, current_batch, total_batches, total_papers):
    return (
        f"You are an expert research analyst processing batch {current_batch} of {total_batches} for the query: '{query}'\n"
        f"Total papers across all batches: {total_papers}. This batch contains {batch_size} papers.\n\n"
        f"Analyze each paper's TITLE carefully to understand its specific focus. "
        f"Write a UNIQUE explanation for EACH paper based on its actual title content. "
        f"Explain HOW each paper's specific topic/method relates to '{query}'. "
        f"Be SPECIFIC about what each paper contributes. "
        f"Each explanation must be different - analyze the actual research focus from the title.\n\n"
        f"For each paper, provide:\n"
        f"1. What specific aspect of '{query}' does this paper address?\n"
        f"2. What methodology, tool, or approach does it present?\n"
        f"3. Why would this be valuable for '{query}' research?\n\n"
        f"Return a JSON array with ALL {batch_size} papers, each having:\n"
        "- title: exact title from input\n"
        "- authors: exact authors from input\n"
        "- explanation: SPECIFIC 2-3 sentences analyzing this paper's unique contribution\n\n"
        f"Papers to analyze:\n{papers_json}\n\n"
        f"Return ONLY a JSON array with ALL {batch_size} papers:"
    )

def citation_ranking_prompt(query, batch_size, papers_json, current_batch, total_batches, total_papers):
    return (
        f"You are an expert research analyst processing batch {current_batch} of {total_batches} for the query: '{query}'\n"
        f"Total papers across all batches: {total_papers}. This batch contains {batch_size} papers.\n\n"
        f"Analyze each paper's TITLE carefully to understand its specific research focus. "
        f"Consider both citation impact and title-based relevance to '{query}'. "
        f"Write a UNIQUE explanation for EACH paper based on its actual title and citation count. "
        f"Explain HOW each paper's specific methodology/tool relates to '{query}'. "
        f"Mention why its citation count indicates importance in the field.\n\n"
        f"For each paper, provide:\n"
        f"1. What specific aspect/method of '{query}' does this paper focus on?\n"
        f"2. How do its citations reflect its impact in '{query}' research?\n"
        f"3. What makes this paper's approach unique or influential?\n\n"
        f"Return a JSON array with ALL {batch_size} papers, each having:\n"
        "- title: exact title from input\n"
        "- authors: exact authors from input\n"
        "- citations: citation count from input\n"
        "- explanation: SPECIFIC analysis of this paper's unique focus and citation impact\n\n"
        f"Papers to analyze:\n{papers_json}\n\n"
        f"Return ONLY a JSON array with ALL {batch_size} papers:"
    )

def ai_description_prompt(query, papers_json):
    return f"""You are an expert research analyst. For each paper below, provide a specific, unique explanation of why it's relevant to the query "{query}".

Each explanation must be 40-80 words. Focus on specific methodologies, findings, or contributions. Be concrete about the paper's unique value for the query. Make each explanation completely different in style and approach.

Papers to analyze:
{papers_json}

Return ONLY a JSON array with explanations in the same order:
[
  {{"explanation": "Specific explanation here"}},
  {{"explanation": "Another unique explanation"}}
]"""
