from typing import Dict, Any, Optional
from ..services.search_service import SearchService
from ..services.paper_service import PaperService
from ..services.ai_service import AIService
from ..providers import provider_registry
from ..config.settings import Settings

class ServiceFactory:
    """Factory for creating and managing services with proper dependencies"""
    
    def __init__(self):
        self.services: Dict[str, Any] = {}
        self._initialized = False
    
    def initialize_services(self, config: Optional[Any] = None) -> None:
        """Initialize all services with their dependencies"""
        if self._initialized:
            return
        
        # Use default config if none provided
        if config is None:
            config = Settings()
        
        # Initialize providers first
        provider_registry.initialize_providers(config)
        
        # Create services with provider dependencies
        self._create_search_service()
        self._create_ai_service()
        self._create_paper_service()
        
        self._initialized = True
        print(f"Initialized {len(self.services)} services")
    
    def _create_search_service(self) -> None:
        """Create search service with search providers"""
        search_providers = provider_registry.get_all_search_providers()
        
        if search_providers:
            default_backend = 'semantic_scholar' if 'semantic_scholar' in search_providers else list(search_providers.keys())[0]
            self.services['search'] = SearchService(search_providers, default_backend)
            print(f"Created SearchService with {len(search_providers)} providers")
        else:
            print("Warning: No search providers available")
    
    def _create_ai_service(self) -> None:
        """Create AI service with AI provider"""
        ai_provider = provider_registry.get_ai_provider()
        
        if ai_provider:
            self.services['ai'] = AIService(ai_provider)
            print(f"Created AIService with provider: {ai_provider.get_provider_name()}")
        else:
            print("Warning: No AI providers available")
    
    def _create_paper_service(self) -> None:
        """Create paper service with all necessary dependencies"""
        # Get legacy search functions for backward compatibility
        from ..paper_search import BACKENDS
        
        ai_provider = provider_registry.get_ai_provider()
        ranking_provider = None  # TODO: Implement ranking provider
        
        if BACKENDS:
            # Create service even without AI provider - will use AI bridge fallback
            self.services['paper'] = PaperService(BACKENDS, ai_provider, ranking_provider)
            if ai_provider:
                print(f"Created PaperService with {len(BACKENDS)} legacy backends and AI provider: {ai_provider.get_provider_name()}")
            else:
                print(f"Created PaperService with {len(BACKENDS)} legacy backends (using AI bridge fallback)")
        else:
            print("Warning: Cannot create PaperService - no search backends available")
    
    def get_service(self, name: str) -> Optional[Any]:
        """Get a service by name"""
        return self.services.get(name)
    
    def get_search_service(self) -> Optional[SearchService]:
        """Get the search service"""
        return self.services.get('search')
    
    def get_ai_service(self) -> Optional[AIService]:
        """Get the AI service"""
        return self.services.get('ai')
    
    def get_paper_service(self) -> Optional[PaperService]:
        """Get the paper service"""
        return self.services.get('paper')
    
    def get_all_services(self) -> Dict[str, Any]:
        """Get all services"""
        return self.services.copy()
    
    def is_initialized(self) -> bool:
        """Check if services have been initialized"""
        return self._initialized

# Global service factory
service_factory = ServiceFactory()
