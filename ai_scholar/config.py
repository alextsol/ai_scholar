import os
from dotenv import load_dotenv

load_dotenv()

SEMANTIC_SCHOLAR_API_URL = os.getenv("SEMANTIC_SCHOLAR_API_URL", "https://api.semanticscholar.org/graph/v1/paper/search")
CROSSREF_API_URL = os.getenv("CROSSREF_API_URL", "https://api.crossref.org/works")
CORE_API_URL = os.getenv("CORE_API_URL", "https://api.core.ac.uk/v3/search/works")

DEFAULT_SEARCH_BACKEND = os.getenv("DEFAULT_SEARCH_BACKEND", "semantic_scholar")

CORE_API_KEY = os.getenv("CORE_API_KEY")

OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENCITATION_API_KEY = os.getenv("OPENCITATION_API_KEY")
