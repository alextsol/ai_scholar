import os
from dotenv import load_dotenv

load_dotenv()  

SEMANTIC_SCHOLAR_API_URL = os.getenv("SEMANTIC_SCHOLAR_API_URL", "https://api.semanticscholar.org/graph/v1/paper/search")
CROSSREF_API_URL = os.getenv("CROSSREF_API_URL", "https://api.crossref.org/works")
CORE_API_URL = os.getenv("CORE_API_URL", "https://api.core.ac.uk/v3/search/works")
IEEE_API_URL = os.getenv("IEEE_API_URL", "http://ieeexploreapi.ieee.org/api/v1/search/articles")

DEFAULT_SEARCH_BACKEND = os.getenv("DEFAULT_SEARCH_BACKEND", "semantic_scholar")

CORE_API_KEY = os.getenv("CORE_API_KEY", "YOUR_CORE_API_KEY")
IEEE_API_KEY = os.getenv("IEEE_API_KEY", "YOUR_IEEE_API_KEY")

DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.ai/rank")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "YOUR_DEEPSEEK_API_KEY")

# GeoIP Database path
GEOIP_DATABASE_PATH = os.getenv("GEOIP_DATABASE_PATH", "data/GeoLite2-City.mmdb")
