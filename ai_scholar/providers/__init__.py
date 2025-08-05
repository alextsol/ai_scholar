from typing import Dict, List, Optional, Any
from ..interfaces.search_interface import ISearchProvider
from ..interfaces.ai_interface import IAIProvider
from ..interfaces.cache_interface import ICacheProvider
from ..interfaces.ranking_interface import IRankingProvider

# Search providers
from .arxiv_search_provider import ArxivSearchProvider
from .semantic_scholar_provider import SemanticScholarProvider
from .crossref_provider import CrossRefProvider
from .core_provider import COREProvider
from .openalex_provider import OpenAlexProvider

# AI providers
from .ai.gemini_provider import GeminiProvider
from .ai.openrouter_provider import OpenRouterProvider

class ProviderRegistry:
    """Registry for managing all providers"""
    
    def __init__(self):
        self.search_providers: Dict[str, ISearchProvider] = {}
        self.ai_providers: Dict[str, IAIProvider] = {}
        self.cache_providers: Dict[str, ICacheProvider] = {}
        self.ranking_providers: Dict[str, IRankingProvider] = {}
        self._initialized = False
    
    def initialize_providers(self, config: Any):
        """Initialize all providers with configuration"""
        if self._initialized:
            return
        
        # Initialize search providers
        self._init_search_providers(config)
        
        # Initialize AI providers  
        self._init_ai_providers(config)
        
        # Initialize cache providers
        self._init_cache_providers(config)
        
        # Initialize ranking providers
        self._init_ranking_providers(config)
        
        self._initialized = True
    
    def _init_search_providers(self, config: Any):
        """Initialize search providers"""
        self.search_providers['arxiv'] = ArxivSearchProvider()
        
        semantic_api_key = getattr(config, 'SEMANTIC_SCHOLAR_API_KEY', None)
        self.search_providers['semantic_scholar'] = SemanticScholarProvider(semantic_api_key)
        
        crossref_api_key = getattr(config, 'CROSSREF_API_KEY', None)
        crossref_mailto = getattr(config, 'CROSSREF_MAILTO', None)
        self.search_providers['crossref'] = CrossRefProvider(crossref_api_key, crossref_mailto)
        
        core_api_key = getattr(config, 'CORE_API_KEY', None)
        self.search_providers['core'] = COREProvider(core_api_key)
        
        openalex_mailto = getattr(config, 'OPENALEX_MAILTO', 'support@ai-scholar.com')
        self.search_providers['openalex'] = OpenAlexProvider(openalex_mailto)
    
    def _init_ai_providers(self, config: Any):
        """Initialize AI providers"""
        from ..config import AIConfig
        
        google_api_keys = [key for key in AIConfig.GOOGLE_API_KEYS if key]
        if google_api_keys:
            for i, api_key in enumerate(google_api_keys):
                provider_name = f'gemini_key_{i+1}'
                try:
                    self.ai_providers[provider_name] = GeminiProvider(
                        api_key=api_key, 
                        model_name=AIConfig.GEMINI_MODEL
                    )
                except Exception as e:
                    pass
        
        if AIConfig.OPENROUTER_API_KEY:
            try:
                self.ai_providers['openrouter'] = OpenRouterProvider(
                    api_key=AIConfig.OPENROUTER_API_KEY,
                    model_name=AIConfig.OPENROUTER_MODEL
                )
            except Exception as e:
                pass
    
    def _init_cache_providers(self, config: Any):
        """Initialize cache providers"""
        pass
    
    def _init_ranking_providers(self, config: Any):
        """Initialize ranking providers"""
        pass
    
    def get_search_provider(self, name: str) -> Optional[ISearchProvider]:
        """Get a search provider by name"""
        return self.search_providers.get(name)
    
    def get_ai_provider(self, name: str = None) -> Optional[IAIProvider]:
        """Get an AI provider by name or the first available one"""
        if name:
            return self.ai_providers.get(name)
        
        for provider in self.ai_providers.values():
            if provider.is_available():
                return provider
        
        return None
    
    def get_all_search_providers(self) -> Dict[str, ISearchProvider]:
        """Get all search providers"""
        return self.search_providers.copy()
    
    def get_all_ai_providers(self) -> Dict[str, IAIProvider]:
        """Get all AI providers"""
        return self.ai_providers.copy()
    
    def get_available_search_backends(self) -> List[str]:
        """Get list of available search backend names"""
        return [
            name for name, provider in self.search_providers.items()
            if provider.is_available()
        ]
    
    def get_available_ai_providers(self) -> List[str]:
        """Get list of available AI provider names"""
        return [
            name for name, provider in self.ai_providers.items()
            if provider.is_available()
        ]
    
    def is_initialized(self) -> bool:
        """Check if providers have been initialized"""
        return self._initialized

# Global provider registry
provider_registry = ProviderRegistry()
