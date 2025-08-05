from enum import Enum

class SearchMode(Enum):
    REGULAR = "regular"
    AGGREGATE = "aggregate"
    
class RankingMode(Enum):
    AI = "ai"
    CITATIONS = "citations"
    YEAR = "year"
    