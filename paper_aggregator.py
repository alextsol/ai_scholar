import openai
import json
from paper_search import BACKENDS
from collections import Counter
from config import DEEPSEEK_API_URL, DEEPSEEK_API_KEY


def aggregate_and_rank_papers(query, limit=10):
    aggregated_papers = []
    for backend_name, backend_func in BACKENDS.items():
        try:
            papers = backend_func(query, limit)
            if isinstance(papers, str) or not papers:
                print(f"Skipping backend '{backend_name}': no valid papers returned.")
                continue 
            aggregated_papers.extend(papers)
        except Exception as e:
            print(f"Error with backend '{backend_name}': {e}")
    if not aggregated_papers:
        return []
    aggregated_papers = remove_duplicates(aggregated_papers)

    bias_report = check_bias_in_aggregated_papers(aggregated_papers)
    print("Bias Report (proportion by source):", json.dumps(bias_report, indent=2))

    return deepseek_rank_papers(query, aggregated_papers)

def deepseek_rank_papers(query, papers):

    try:
        papers_json = json.dumps(papers, indent=2)
        messages = [
            {
                "role": "system",
                "content": (
                    "You are DeepSeek, a specialized AI assistant for evaluating and ranking scholarly papers. "
                    "You have been given a list of papers, each containing a title, abstract, authors, publication year, and URL."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Based on the query '{query}', please review the following list of papers and determine "
                    "which 10 are the most relevant and high-quality. For each of your top 10 selections, provide a brief explanation "
                    "of why that paper is important or particularly relevant to the query. "
                    "Return your output as a JSON array where each element is an object with the keys: 'title', 'authors', 'year', 'url', and 'reason'. "
                    "Here is the list:\n\n" + papers_json
                )
            }
        ]

        response = openai.ChatCompletion.create(
            model="deepseek-chat",
            messages=messages,
            stream=False
        )

        ranked_response = response['choices'][0]['message']['content']
        ranked_papers = json.loads(ranked_response)
        return ranked_papers[:10]
    except Exception as e:
        print(f"Error in DeepSeek chat completion: {e}")
        return papers

def remove_duplicates(papers):
    seen = set()
    unique_papers = []
    for paper in papers:
        key = (paper.get('title'), paper.get('year'))
        if key not in seen:
            seen.add(key)
            unique_papers.append(paper)
    return unique_papers

def check_bias_in_aggregated_papers(papers):
    sources = [paper.get('source', 'unknown') for paper in papers]
    counts = Counter(sources)
    total = len(papers)
    bias_report = {src: count/total for src, count in counts.items()}
    return bias_report

if __name__ == "__main__":

    query = input("Enter your search query: ")
    ranked = aggregate_and_rank_papers(query)
    print(json.dumps(ranked, indent=2))
