from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class IAIProvider(ABC):
    """Abstract interface for AI providers (Google Gemini, OpenRouter, etc.)"""
    
    @abstractmethod
    def generate_content(self, prompt: str, operation_type: str = "general") -> Optional[str]:
        """
        Generate AI content from a prompt
        
        Args:
            prompt: The input prompt for the AI
            operation_type: Type of operation (ranking, description, etc.)
            
        Returns:
            Generated text content or None if failed
        """
        pass
    
    @abstractmethod
    def process_batch(self, prompt: str, batch_num: int, total_batches: int, operation_type: str) -> Optional[List[Dict[str, Any]]]:
        """
        Process a batch of papers with AI
        
        Args:
            prompt: The batch processing prompt
            batch_num: Current batch number
            total_batches: Total number of batches
            operation_type: Type of batch operation
            
        Returns:
            List of processed results or None if failed
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        pass
    
    @abstractmethod
    def get_optimal_batch_size(self, operation_type: str = "general") -> int:
        pass
