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
        
        if config is None:
            config = Settings()
        
        provider_registry.initialize_providers(config)
        
        self._create_search_service()
        self._create_ai_service()
        self._create_paper_service()
        
        self._initialized = True
    
    def _create_search_service(self) -> None:
        """Create search service with search providers"""
        search_providers = provider_registry.get_all_search_providers()
        
        if search_providers:
            default_backend = 'semantic_scholar' if 'semantic_scholar' in search_providers else list(search_providers.keys())[0]
            self.services['search'] = SearchService(search_providers, default_backend)
    
    def _create_ai_service(self) -> None:
        """Create AI service with AI provider"""
        ai_provider = provider_registry.get_ai_provider()
        
        if ai_provider:
            self.services['ai'] = AIService(ai_provider)
    
    def _create_paper_service(self) -> None:
        """Create paper service with search and AI providers"""
        backends = {}
        search_providers = provider_registry.get_all_search_providers()
        
        for name, provider in search_providers.items():
            def create_search_func(p):
                def search_func(query, max_results=10, min_year=None, max_year=None):
                    try:
                        # Call provider's search method with individual parameters
                        result = p.search(
                            query=query,
                            limit=max_results,
                            min_year=min_year,
                            max_year=max_year
                        )
                        return result if result else []
                    except Exception as e:
                        return []
                return search_func
            
            backends[name] = create_search_func(provider)
        
        ai_provider = provider_registry.get_ai_provider()
        ranking_provider = None
        
        if backends:
            self.services['paper'] = PaperService(backends, ai_provider, ranking_provider)
    
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

service_factory = ServiceFactory()
