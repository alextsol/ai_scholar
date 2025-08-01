"""
Input validation utilities
"""
import re
from typing import Optional
from .exceptions import ValidationError

def validate_query(query: str) -> str:
    """
    Validate and clean search query
    
    Args:
        query: Raw search query string
        
    Returns:
        Cleaned query string
        
    Raises:
        ValidationError: If query is invalid
    """
    if not query or not isinstance(query, str):
        raise ValidationError("Query must be a non-empty string")
    
    cleaned_query = query.strip()
    
    if len(cleaned_query) == 0:
        raise ValidationError("Query cannot be empty")
    
    if len(cleaned_query) > 500:
        raise ValidationError("Query too long (max 500 characters)")
    
    # Remove excessive whitespace
    cleaned_query = re.sub(r'\s+', ' ', cleaned_query)
    
    return cleaned_query

def validate_year_range(min_year: Optional[int], max_year: Optional[int]) -> tuple[Optional[int], Optional[int]]:
    """
    Validate year range for search filters
    
    Args:
        min_year: Minimum year (optional)
        max_year: Maximum year (optional)
        
    Returns:
        Tuple of validated (min_year, max_year)
        
    Raises:
        ValidationError: If year range is invalid
    """
    if min_year is not None:
        if not isinstance(min_year, int) or min_year < 1900:
            raise ValidationError("Minimum year must be an integer >= 1900")
    
    if max_year is not None:
        if not isinstance(max_year, int) or max_year > 2030:
            raise ValidationError("Maximum year must be an integer <= 2030")
    
    if min_year is not None and max_year is not None:
        if min_year > max_year:
            raise ValidationError("Minimum year cannot be greater than maximum year")
    
    return min_year, max_year

def validate_limit(limit: int, max_limit: int = 1000) -> int:
    """
    Validate result limit
    
    Args:
        limit: Number of results requested
        max_limit: Maximum allowed limit
        
    Returns:
        Validated limit
        
    Raises:
        ValidationError: If limit is invalid
    """
    if not isinstance(limit, int) or limit <= 0:
        raise ValidationError("Limit must be a positive integer")
    
    if limit > max_limit:
        raise ValidationError(f"Limit cannot exceed {max_limit}")
    
    return limit

def validate_ranking_mode(ranking_mode: str) -> str:
    """
    Validate ranking mode
    
    Args:
        ranking_mode: Ranking mode string
        
    Returns:
        Validated ranking mode
        
    Raises:
        ValidationError: If ranking mode is invalid
    """
    valid_modes = ["ai_ranking", "citation_ranking"]
    
    if not isinstance(ranking_mode, str):
        raise ValidationError("Ranking mode must be a string")
    
    if ranking_mode not in valid_modes:
        raise ValidationError(f"Ranking mode must be one of: {valid_modes}")
    
    return ranking_mode
