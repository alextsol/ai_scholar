def ai_ranking_prompt(query, batch_size, papers_json, current_batch, total_batches, total_papers):
    """Create AI ranking prompt with batch information"""
    return (
        f"You are processing batch {current_batch} of {total_batches} for the query: '{query}'\n"
        f"Total papers across all batches: {total_papers}. This batch contains {batch_size} papers.\n\n"
        f"IMPORTANT: Provide explanations for ALL {batch_size} papers in this batch, not just the top ones.\n"
        f"For each paper, provide a detailed explanation (2-3 sentences) of why it's relevant to the query.\n\n"
        f"Return a JSON array with ALL {batch_size} papers, each having:\n"
        "- title: exact title from input (use 't' field value)\n"
        "- authors: exact authors from input (use 'a' field value)\n"
        "- explanation: detailed 2-3 sentence explanation of relevance\n\n"
        f"Papers to analyze:\n{papers_json}\n\n"
        f"Return ONLY a JSON array with ALL {batch_size} papers:"
    )

def citation_ranking_prompt(query, batch_size, papers_json, current_batch, total_batches, total_papers):
    """Create citation ranking prompt with batch information"""
    return (
        f"You are processing batch {current_batch} of {total_batches} for the query: '{query}'\n"
        f"Total papers across all batches: {total_papers}. This batch contains {batch_size} papers.\n\n"
        f"IMPORTANT: Provide explanations for ALL {batch_size} papers in this batch.\n"
        f"Consider both citation count ('c' field) and relevance to the query.\n"
        f"For each paper, provide a detailed explanation (2-3 sentences) considering both citations and relevance.\n\n"
        f"Return a JSON array with ALL {batch_size} papers, each having:\n"
        "- title: exact title from input (use 't' field value)\n"
        "- authors: exact authors from input (use 'a' field value)\n"
        "- citations: citation count from input (use 'c' field value)\n"
        "- explanation: detailed explanation of citation impact and relevance\n\n"
        f"Papers to analyze:\n{papers_json}\n\n"
        f"Return ONLY a JSON array with ALL {batch_size} papers:"
    )
