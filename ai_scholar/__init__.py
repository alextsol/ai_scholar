"""
AI Scholar - Academic Paper Search and Ranking System
"""
from .search_api import AIScholar
from .config import AIConfig, SearchConfig, AppConfig

__version__ = "2.0.0"
__all__ = ["AIScholar", "AIConfig", "SearchConfig", "AppConfig"]
