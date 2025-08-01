"""
Configuration management package
"""
from .settings import Settings
from .providers_config import ProvidersConfig
from .database_config import DatabaseConfig

# Backward compatibility aliases
AIConfig = ProvidersConfig.AI
SearchConfig = Settings
AppConfig = Settings

__all__ = ["Settings", "ProvidersConfig", "DatabaseConfig", "AIConfig", "SearchConfig", "AppConfig"]
