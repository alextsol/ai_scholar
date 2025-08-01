"""
AI Bridge for the new architecture
Provides compatibility layer for existing code while using new services
"""

from typing import Optional, Dict, Any, List
from .ai_models import ai_models  # Existing AI model manager
from .providers import provider_registry
from .services.service_factory import service_factory

class AIBridge:
    """Bridge to new provider architecture"""
    
    def __init__(self):
        self._ai_service = None
        self._initialized = False
    
    def initialize(self):
        """Initialize the bridge with new architecture"""
        try:
            # Get new AI service
            self._ai_service = service_factory.get_ai_service()
            if self._ai_service:
                self._initialized = True
                print("AI Bridge: Using new architecture")
            else:
                print("AI Bridge: Warning - AI service not available")
        except Exception as e:
            print(f"AI Bridge: Error initializing: {e}")
    
    def generate_content(self, prompt: str, operation_type: str = "general") -> Optional[str]:
        """Generate content using new architecture"""
        if self._initialized and self._ai_service:
            try:
                return self._ai_service.generate_content(prompt, operation_type=operation_type)
            except Exception as e:
                print(f"AI Bridge: Content generation failed: {e}")
                return None
        
        # Use legacy AI models as last resort
        return ai_models.generate_content(prompt, operation_type)
    
    def rank_papers(self, query: str, papers: List[Dict[str, Any]], ranking_mode: str = 'ai', limit: int = 10) -> List[Dict[str, Any]]:
        """Rank papers using new architecture"""
        if self._initialized and self._ai_service:
            try:
                return self._ai_service.rank_papers(query, papers, ranking_mode, limit)
            except Exception as e:
                print(f"AI Bridge: Paper ranking failed: {e}")
                return papers[:limit]  # Return unranked papers as fallback
        
        # Return unranked papers if no AI service available
        return papers[:limit]
    
    def process_batch(self, prompt: str, batch_num: int, total_batches: int, operation_type: str) -> Optional[List[Dict[str, Any]]]:
        """Process batch using new architecture"""
        if self._initialized and self._ai_service:
            try:
                # New system doesn't have direct batch processing, use generate_content
                response = self._ai_service.generate_content(prompt, operation_type=f"{operation_type}_batch")
                if response:
                    from .utils.ai_utils import parse_ai_response
                    return parse_ai_response(response)
            except Exception as e:
                print(f"AI Bridge: Batch processing failed: {e}")
                return None
        
        # Use legacy system for batch processing
        return ai_models.process_batch(prompt, batch_num, total_batches, operation_type)
    
    def get_optimal_batch_size(self, operation_type: str = "general") -> int:
        """Get optimal batch size"""
        # Use legacy system as it has this logic
        return ai_models.get_optimal_batch_size(operation_type)
    
    def is_available(self) -> bool:
        """Check if AI system is available"""
        if self._initialized and self._ai_service:
            ai_provider = provider_registry.get_ai_provider()
            return ai_provider.is_available() if ai_provider else False
        
        # Check legacy system
        return len(ai_models.available_models) > 0

# Global AI bridge instance
ai_bridge = AIBridge()
