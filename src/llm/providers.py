"""LLM Provider Registry

This module registers all available LLM providers.
"""

from .provider import OpenAIProvider, AnthropicProvider, GeminiProvider
from .novelai_provider import NovelAIProvider

PROVIDERS = {
    'openai': OpenAIProvider,
    'anthropic': AnthropicProvider,
    'gemini': GeminiProvider,
    'novelai': NovelAIProvider
}

def get_provider(config: dict) -> 'LLMProvider':
    """Get the appropriate provider based on configuration.
    
    Args:
        config: Provider configuration dictionary
        
    Returns:
        Configured LLM provider instance
        
    Raises:
        ValueError: If provider is not supported
    """
    provider_name = config.get('provider', '').lower()
    
    if provider_name in PROVIDERS:
        return PROVIDERS[provider_name](config)
    else:
        raise ValueError(f"Unsupported provider: {provider_name}")
