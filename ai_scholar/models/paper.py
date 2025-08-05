from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class Paper:
    """Data model for academic papers"""
    
    title: str
    authors: str
    abstract: Optional[str] = None
    year: Optional[int] = None
    url: Optional[str] = None
    citations: Optional[int] = None
    source: Optional[str] = None
    published: Optional[str] = None
    
    # AI-generated fields
    explanation: Optional[str] = None
    ai_relevance_score: Optional[int] = None
    final_relevance_score: Optional[float] = None
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert paper to dictionary"""
        return {
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "year": self.year,
            "url": self.url,
            "citations": self.citations,
            "source": self.source,
            "published": self.published,
            "explanation": self.explanation,
            "ai_relevance_score": self.ai_relevance_score,
            "final_relevance_score": self.final_relevance_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Paper':
        """Create paper from dictionary"""
        created_at = None
        updated_at = None
        
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])
        if data.get('updated_at'):
            updated_at = datetime.fromisoformat(data['updated_at'])
            
        return cls(
            title=data.get('title', ''),
            authors=data.get('authors', ''),
            abstract=data.get('abstract'),
            year=data.get('year'),
            url=data.get('url'),
            citations=data.get('citations'),
            source=data.get('source'),
            published=data.get('published'),
            explanation=data.get('explanation'),
            ai_relevance_score=data.get('ai_relevance_score'),
            final_relevance_score=data.get('final_relevance_score'),
            created_at=created_at,
            updated_at=updated_at
        )
    
    def has_complete_metadata(self) -> bool:
        """Check if paper has complete metadata"""
        return all([
            self.title and len(self.title.strip()) > 0,
            self.authors and len(self.authors.strip()) > 0,
            self.abstract and len(self.abstract.strip()) > 10,
            self.year and self.year > 1900,
        ])
