class PaperIndexer:
    @staticmethod
    def create_arxiv_index(papers):
        """Create index mapping arXiv IDs to paper positions"""
        arxiv_id_to_index = {}
        arxiv_ids = []
        
        for idx, paper in enumerate(papers):
            if not isinstance(paper, dict):
                continue
                
            arxiv_id = paper.get('roi')
            if arxiv_id:
                arxiv_ids.append(arxiv_id)
                arxiv_id_to_index[arxiv_id] = idx
        
        return arxiv_ids, arxiv_id_to_index
    
    @staticmethod
    def has_arxiv_papers(papers):
        """Check if any papers have arXiv IDs"""
        for paper in papers:
            if isinstance(paper, dict) and paper.get('roi'):
                return True
        return False