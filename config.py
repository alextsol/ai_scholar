import os
from dotenv import load_dotenv

load_dotenv()  

SEMANTIC_SCHOLAR_API_URL = os.getenv("SEMANTIC_SCHOLAR_API_URL", "https://api.semanticscholar.org/graph/v1/paper/search")
CROSSREF_API_URL = os.getenv("CROSSREF_API_URL", "https://api.crossref.org/works")
CORE_API_URL = os.getenv("CORE_API_URL", "https://api.core.ac.uk/v3/search/works")
IEEE_API_URL = os.getenv("IEEE_API_URL", "http://ieeexploreapi.ieee.org/api/v1/search/articles")

DEFAULT_SEARCH_BACKEND = os.getenv("DEFAULT_SEARCH_BACKEND", "semantic_scholar")

CORE_API_KEY = os.getenv("CORE_API_KEY", "QD9qUjnImpTE1MxFZWvlkRXyBt8ShA54")
#10,000 tokens per day
IEEE_API_KEY = os.getenv("IEEE_API_KEY", "x5znkb5cx9tcq4q4vmestcap")
#limit 200/day

DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/rank")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-e640d7b0cee041048012470d986f0eae")

# GeoIP Database path
GEOIP_DATABASE_PATH = os.getenv("GEOIP_DATABASE_PATH", "data/GeoLite2-City.mmdb")
