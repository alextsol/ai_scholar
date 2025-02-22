import requests
from paper_search import BACKENDS
from config import DEEPSEEK_API_URL, DEEPSEEK_API_KEY

def aggregate_and_rank_papers(query, limit=10):
    aggregated_papers = []
    for backend_name, backend_func in BACKENDS.items():
        try:
            papers = backend_func(query, limit)
            if isinstance(papers, str):
                continue 
            aggregated_papers.extend(papers)
        except Exception as e:
            print(f"Error with {backend_name}: {e}")
    if not aggregated_papers:
        return []
    aggregated_papers = remove_duplicates(aggregated_papers)
    return deepseek_rank_papers(query, aggregated_papers)

def deepseek_rank_papers(query, papers):
    payload = {
        "query": query,
        "papers": papers
    }
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers)
    if response.status_code != 200:
        print(f"DeepSeek API error: {response.status_code}")
        return papers
    data = response.json()
    return data.get("ranked_papers", papers)

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
    query = "machine learning"
    ranked = aggregate_and_rank_papers(query)
    print(ranked)
