import requests
import logging
import time

logger = logging.getLogger(__name__)

class SemanticScholarAPI:
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    
    def __init__(self, batch_size=25, delay=1):
        self.batch_size = batch_size
        self.delay = delay
        self.headers = {'Content-Type': 'application/json'}
    
    def fetch_papers_batch(self, arxiv_ids):
        """Fetch a batch of papers from Semantic Scholar API"""
        payload = {"ids": [f"ARXIV:{arxiv_id}" for arxiv_id in arxiv_ids]}
        
        try:
            response = requests.post(
                f"{self.BASE_URL}/paper/batch?fields=title,citationCount,externalIds",
                json=payload,
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                return data if isinstance(data, list) else data.get('data', [])
            else:
                logger.error(f"Semantic Scholar API Error: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Semantic Scholar Exception: {e}")
            return []
    
    def fetch_all_papers(self, arxiv_ids):
        """Fetch all papers in batches"""
        all_papers = []
        
        for i in range(0, len(arxiv_ids), self.batch_size):
            batch_ids = arxiv_ids[i:i + self.batch_size]
            papers = self.fetch_papers_batch(batch_ids)
            all_papers.extend(papers)
            
            # Add delay between batches
            if i + self.batch_size < len(arxiv_ids):
                time.sleep(self.delay)
        
        return all_papers