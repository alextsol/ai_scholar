import logging

logger = logging.getLogger(__name__)

class CitationMatcher:
    @staticmethod
    def extract_arxiv_id_from_paper(paper_data):
        """Extract arXiv ID from Semantic Scholar paper data"""
        external_ids = paper_data.get('externalIds', {})
        if 'arxiv' in external_ids:
            arxiv_id = external_ids['arxiv']
            return arxiv_id[0] if isinstance(arxiv_id, list) else arxiv_id
        return None
    
    @staticmethod
    def match_by_title(paper_data, papers, arxiv_id_to_index):
        """Match paper by title when arXiv ID is not available"""
        title = paper_data.get('title', '').strip().lower()
        for aid, idx in arxiv_id_to_index.items():
            if papers[idx].get('title', '').strip().lower() == title:
                return aid
        return None
    
    @staticmethod
    def update_paper_citation(papers, arxiv_id_to_index, arxiv_id, citation_count):
        """Update citation count for a specific paper"""
        idx = arxiv_id_to_index.get(arxiv_id)
        if idx is not None:
            papers[idx]['citation'] = int(citation_count)
            return True
        return False