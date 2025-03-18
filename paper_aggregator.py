import requests
import json
from paper_search import BACKENDS
from config import DEEPSEEK_API_URL, DEEPSEEK_API_KEY
from fairness import compute_fairness_metrics

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
    
    # Compute fairness metrics
    fairness_report = compute_fairness_metrics(aggregated_papers)
    print("Fairness Report (mean score by source):", json.dumps(fairness_report, indent=2))
    
    return deepseek_rank_papers(query, aggregated_papers)

def deepseek_rank_papers(query, papers):
    payload = {
        "query": query,
        "papers": papers,
        "top": 10
    }
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"DeepSeek API error: {response.status_code}")
            return papers[:10]
        data = response.json()
        ranked = data.get("ranked_papers", None)
        if not ranked:
            print("DeepSeek API did not return ranked papers, returning top 10 aggregated papers.")
            return papers[:10]
        return ranked[:10]
    except Exception as e:
        print(f"DeepSeek ranking exception: {e}")
        return papers[:10]

def remove_duplicates(papers):
    seen = set()
    unique_papers = []
    for paper in papers:
        key = (paper.get('title'), paper.get('year'))
        if key not in seen:
            seen.add(key)
            unique_papers.append(paper)
    return unique_papers

if __name__ == "__main__":
    query = input("Enter your search query: ")
    ranked = aggregate_and_rank_papers(query)
    print(json.dumps(ranked, indent=2))
