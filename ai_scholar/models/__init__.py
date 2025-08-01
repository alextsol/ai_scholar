"""
Data models package - DTOs and domain models
"""
from .paper import Paper
from .search_request import SearchRequest
from .search_result import SearchResult
from .database import db, User, SearchHistory

__all__ = ["Paper", "SearchRequest", "SearchResult", "db", "User", "SearchHistory"]
