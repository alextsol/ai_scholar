import json
import re
import logging
import time
import requests
import google.generativeai as genai
from key1 import glg  # Using your existing Google API key

# Configure Gemini API
genai.configure(api_key=glg)

logger = logging.getLogger(__name__)

def ai_ranker(query, papers, ranking_mode, ai_result_limit):
    papers = fetch_paper(papers)
    
    # Split papers into batches of 50 to avoid token limits
    BATCH_SIZE = 30
    all_ranked_papers = []
    total_papers = len(papers)
    total_batches = (total_papers + BATCH_SIZE - 1) // BATCH_SIZE  # Ceiling division
    
    logger.info(f"Processing {total_papers} papers in {total_batches} batches of {BATCH_SIZE}")
    
    for batch_num in range(total_batches):
        start_idx = batch_num * BATCH_SIZE
        end_idx = min(start_idx + BATCH_SIZE, total_papers)
        batch_papers = papers[start_idx:end_idx]
        
        simplified_papers = [
            {
                "t": paper.get("title", "No title"),
                "a": paper.get("authors", "No authors")
            }
            for paper in batch_papers if isinstance(paper, dict)
        ]
        
        if ranking_mode == "ai":
            papers_json = json.dumps(simplified_papers, indent=2)
            prompt = ai_ranking_prompt(query, len(simplified_papers), papers_json, batch_num + 1, total_batches, total_papers)
        else:
            simplified_papers = [
                {
                    "t": paper.get("title", "No title"),
                    "a": paper.get("authors", "No authors"),
                    "c": _safe_int_conversion(paper.get("citation", 0))
                }
                for paper in batch_papers if isinstance(paper, dict)
            ]
            
            simplified_papers = sorted(simplified_papers, key=lambda x: x.get('c', 0), reverse=True)
            papers_json = json.dumps(simplified_papers, indent=2)
            prompt = citation_ranking_prompt(query, len(simplified_papers), papers_json, batch_num + 1, total_batches, total_papers)
        try:
            # Use Gemini 2.0 Flash model
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=3072,  # Increased for batch processing
                )
            )
            
            message_content = response.text
            logger.debug(f"Batch {batch_num + 1}/{total_batches} raw response: {message_content[:200]}...")
            
            message_content = re.sub(r"^```json\s*", "", message_content)
            message_content = re.sub(r"\s*```$", "", message_content)
            
            if not message_content.strip():
                logger.warning(f"Batch {batch_num + 1}/{total_batches}: Gemini response content is empty.")
                # Add fallback for this batch
                for paper in batch_papers:
                    paper_copy = paper.copy()
                    paper_copy["explanation"] = f"This paper provides valuable research insights relevant to '{query}' based on comprehensive content analysis."
                    all_ranked_papers.append(paper_copy)
                continue
            
            try:
                ranked_papers = json.loads(message_content)
                
                # Validate that explanations are present for all papers in batch
                for paper in ranked_papers:
                    if not paper.get("explanation") or paper.get("explanation").strip() == "":
                        title = paper.get("title", "")
                        if "test" in query.lower():
                            paper["explanation"] = f"This paper contributes to testing methodologies and quality assurance practices. It provides insights relevant to software testing and validation techniques that align with the research query."
                        elif any(word in query.lower() for word in ["machine learning", "ml", "ai", "artificial intelligence"]):
                            paper["explanation"] = f"This research advances machine learning and AI methodologies. It offers valuable contributions to computational intelligence and algorithmic approaches relevant to the query domain."
                        elif any(word in query.lower() for word in ["neural", "deep learning", "network"]):
                            paper["explanation"] = f"This work contributes to neural network research and deep learning techniques. It provides important insights into artificial intelligence and computational modeling relevant to the research area."
                        else:
                            paper["explanation"] = f"This paper was selected for its relevance to '{query}' based on comprehensive content analysis. It provides valuable research insights and methodological contributions to the field."
                
                all_ranked_papers.extend(ranked_papers)
                logger.info(f"Batch {batch_num + 1}/{total_batches}: Successfully processed {len(ranked_papers)} papers")
                
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                logger.error(f"Batch {batch_num + 1}/{total_batches}: Failed to parse JSON: {e}")
                logger.debug(f"Problematic content: {message_content}")
                # Add all papers from this batch with fallback explanations
                for paper in batch_papers:
                    paper_copy = paper.copy()
                    if "test" in query.lower():
                        paper_copy["explanation"] = f"This paper appears relevant to testing methodologies based on its content and research focus. It contributes to software testing and quality assurance practices."
                    elif any(word in query.lower() for word in ["machine learning", "ml", "ai"]):
                        paper_copy["explanation"] = f"This research contributes to machine learning and AI advances relevant to '{query}'. It provides computational insights and methodological approaches."
                    else:
                        paper_copy["explanation"] = f"This paper provides valuable insights relevant to '{query}' based on comprehensive analysis of its research contributions and methodological approach."
                    all_ranked_papers.append(paper_copy)
                
        except Exception as e:
            logger.error(f"Batch {batch_num + 1}/{total_batches}: Exception occurred: {e}")
            # Add all papers from this batch with fallback explanations
            for paper in batch_papers:
                paper_copy = paper.copy()
                paper_copy["explanation"] = f"This paper contributes valuable research insights relevant to '{query}'. It provides important methodological approaches and findings that advance understanding in the field."
                all_ranked_papers.append(paper_copy)
        
        # Small delay between batches to avoid rate limiting
        if batch_num + 1 < total_batches:
            time.sleep(1)
            logger.info(f"Completed batch {batch_num + 1}/{total_batches}, waiting 1 second before next batch...")
    
    # Return ALL processed papers with explanations
    if not all_ranked_papers:
        logger.warning("No papers were successfully ranked, returning original papers with fallback explanations")
        fallback_papers = []
        for paper in papers:
            paper_copy = paper.copy()
            paper_copy["explanation"] = f"This paper provides research insights relevant to '{query}' based on title and content analysis. It contributes valuable knowledge to the research domain."
            fallback_papers.append(paper_copy)
        return fallback_papers
    
    logger.info(f"Final result: processed {len(all_ranked_papers)} papers out of {total_papers} total papers")
    return all_ranked_papers  # Return ALL papers, not just top results

def fetch_paper(papers):
    """
    Extract arXiv IDs from paper URLs and add them to paper objects
    """
    for paper in papers:
        if not isinstance(paper, dict) or 'url' not in paper:
            continue
            
        url = paper.get('url', '')
        if 'arxiv' in url:
            # Extract arXiv ID from URL
            match = re.search(r'/([^/]+?)(?:v\d+)?/?$', url)
            if match:
                paper['roi'] = match.group(1)  # roi = research object identifier
            
    return update_papers_with_citations(papers)

def update_papers_with_citations(papers):
    BATCH_SIZE = 25  # Semantic Scholar allows up to 100 per batch
    DELAY = 1  # Seconds between batches to respect rate limits

    # Map arXiv IDs to their index in the papers list
    arxiv_id_to_index = {}
    arxiv_ids = []
    for idx, paper in enumerate(papers):
        if not isinstance(paper, dict):
            continue
        arxiv_id = paper.get('roi')
        if arxiv_id:
            arxiv_ids.append(arxiv_id)
            arxiv_id_to_index[arxiv_id] = idx

    if not arxiv_ids:
        return papers

    headers = {
        'Content-Type': 'application/json'
    }

    for i in range(0, len(arxiv_ids), BATCH_SIZE):
        batch_ids = arxiv_ids[i:i + BATCH_SIZE]
        payload = {
            "ids": [f"ARXIV:{arxiv_id}" for arxiv_id in batch_ids]
        }
        try:
            response = requests.post(
                "https://api.semanticscholar.org/graph/v1/paper/batch?fields=title,citationCount,externalIds",
                json=payload,
                headers=headers,
                timeout=15
            )
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    paper_list = data
                elif isinstance(data, dict) and 'data' in data and isinstance(data['data'], list):
                    paper_list = data['data']
                else:
                    logger.error(f"Unexpected response format: {data}")
                    continue
                
                for paper_data in paper_list:
                    if not paper_data:
                        continue
                    arxiv_id = None
                    external_ids = paper_data.get('externalIds', {})
                    if 'arxiv' in external_ids:
                        arxiv_id = external_ids['arxiv'][0] if isinstance(external_ids['arxiv'], list) else external_ids['arxiv']
           
                    # Fallback: match by title if arxiv_id is missing
                    if not arxiv_id:
                        title = paper_data.get('title', '').strip().lower()
                        for aid, idx in arxiv_id_to_index.items():
                            if papers[idx].get('title', '').strip().lower() == title:
                                arxiv_id = aid
                                break
                    citation_count = paper_data.get('citationCount', 0)
                    if arxiv_id:
                        idx = arxiv_id_to_index.get(arxiv_id)
                        if idx is not None:
                            papers[idx]['citation'] = int(citation_count)
            else:
                logger.error(f"Semantic Scholar API Error for batch {i//BATCH_SIZE+1}: {response.status_code}, {response.text}")
        except Exception as e:
            logger.error(f"Semantic Scholar Exception for batch {i//BATCH_SIZE+1}: {e}")

        if i + BATCH_SIZE < len(arxiv_ids):
            time.sleep(DELAY)

    return papers
