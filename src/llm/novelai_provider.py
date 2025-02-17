"""NovelAI Provider Module

This module implements the NovelAI provider for narrative generation.
"""

import os
import asyncio
from typing import Dict, Any, Optional, List
import importlib

from .provider import LLMProvider

# Lazy imports for NovelAI dependencies
def get_novelai_imports():
    """Get NovelAI dependencies, importing only when needed."""
    try:
        BanList = importlib.import_module('novelai_api.BanList').BanList
        BiasGroup = importlib.import_module('novelai_api.BiasGroup').BiasGroup
        GlobalSettings = importlib.import_module('novelai_api.GlobalSettings').GlobalSettings
        Model = importlib.import_module('novelai_api.Preset').Model
        Preset = importlib.import_module('novelai_api.Preset').Preset
        PREAMBLE = importlib.import_module('novelai_api.Preset').PREAMBLE
        Tokenizer = importlib.import_module('novelai_api.Tokenizer').Tokenizer
        b64_to_tokens = importlib.import_module('novelai_api.utils').b64_to_tokens
        API = importlib.import_module('example.boilerplate').API
        return BanList, BiasGroup, GlobalSettings, Model, Preset, PREAMBLE, Tokenizer, b64_to_tokens, API
    except ImportError as e:
        raise ImportError(f"NovelAI dependencies not found. Please install novelai-api package: {str(e)}")

class NovelAIProvider(LLMProvider):
    # Import dependencies only when class is used
    BanList, BiasGroup, GlobalSettings, Model, Preset, PREAMBLE, Tokenizer, b64_to_tokens, API = None, None, None, None, None, None, None, None, None
    """NovelAI-specific LLM provider implementation."""
    
    MODEL_CONFIGS = {
        "erato": {
            "model": "erato",  # Will be converted to Model.Erato when needed
            "max_input_tokens": 16384,
            "max_output_tokens": 4096,
            "bytes_per_token": 4,  # Erato uses 4 bytes per token
            "preset": "Storywriter",
            "subscription": "$20/month unlimited"
        },
        "kayra": {
            "model": "kayra",  # Will be converted to Model.Kayra when needed
            "max_input_tokens": 8192,
            "max_output_tokens": 4096,
            "bytes_per_token": 2,
            "preset": "Storywriter",
            "subscription": "$20/month unlimited"
        },
        "clio": {
            "model": "clio",  # Will be converted to Model.Clio when needed
            "max_input_tokens": 8192,
            "max_output_tokens": 4096,
            "bytes_per_token": 2,
            "preset": "Storywriter",
            "subscription": "$20/month unlimited"
        },
        "krake": {
            "model": "krake",  # Will be converted to Model.Krake when needed
            "max_input_tokens": 8192,
            "max_output_tokens": 4096,
            "bytes_per_token": 2,
            "preset": "Storywriter",
            "subscription": "$20/month unlimited"
        }
    }
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize NovelAI provider.
        
        Args:
            config: NovelAI-specific configuration
            
        Raises:
            ValueError: If model_version is invalid
        """
        model_version = config.get('model_version', 'erato')
        if model_version not in self.MODEL_CONFIGS:
            raise ValueError(f"Invalid model version: {model_version}. Must be one of {list(self.MODEL_CONFIGS.keys())}")
            
        model_config = self.MODEL_CONFIGS[model_version]
        
        # Update config with model-specific settings
        config['model'] = model_config['model']
        config['max_input_tokens'] = model_config['max_input_tokens']
        
        super().__init__(config)
        
        # Store model config for later use
        self.model_config = model_config
        
        # Import dependencies if not already imported
        if NovelAIProvider.API is None:
            (NovelAIProvider.BanList, NovelAIProvider.BiasGroup, NovelAIProvider.GlobalSettings,
             NovelAIProvider.Model, NovelAIProvider.Preset, NovelAIProvider.PREAMBLE,
             NovelAIProvider.Tokenizer, NovelAIProvider.b64_to_tokens, NovelAIProvider.API) = get_novelai_imports()
        
        # Convert string model name to Model enum
        model_enum = getattr(NovelAIProvider.Model, self.model_config['model'].capitalize())
        self.model_config['model'] = model_enum
        
        # Initialize API client
        self.api_handler = NovelAIProvider.API()
        self.api = self.api_handler.api
        
        # Load preset
        self.preset = NovelAIProvider.Preset.from_official(
            self.model_config['model'],
            self.model_config['preset']
        )
        
        # Configure generation settings
        self.preset.min_length = 1
        self.preset.max_length = self.model_config['max_output_tokens']
        
        # Initialize global settings
        self.global_settings = NovelAIProvider.GlobalSettings(
            num_logprobs=NovelAIProvider.GlobalSettings.NO_LOGPROBS
        )
        
        # Optional generation settings
        self.bad_words = None  # Can be configured for content filtering
        self.bias_groups: List[Any] = []  # Can be used for narrative control
        self.module = None  # Can be set for genre-specific generation
        self.stop_sequence = ["\n\n"]  # Default stop sequence for chunking
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using NovelAI's tokenizer.
        
        Args:
            text: Input text to count tokens for
            
        Returns:
            Number of tokens in the text
        """
        return len(NovelAIProvider.Tokenizer.encode(self.model_config['model'], text))
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> Dict[str, float]:
        """Calculate cost for NovelAI token usage.
        
        Note: NovelAI uses a subscription model ($20/month) with unlimited generations.
        Token counts are tracked for informational purposes only.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Dictionary containing cost information
        """
        return {
            'input_cost': 0,  # Unlimited with subscription
            'output_cost': 0, # Unlimited with subscription
            'total_cost': 0,  # $20/month flat rate
            'subscription': "$20/month unlimited"
        }
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text using NovelAI's API.
        
        Args:
            prompt: The main prompt text
            system_prompt: Optional system instructions
            
        Returns:
            Generated text response
            
        Raises:
            Exception: If the API call fails
        """
        # Combine prompts with model preamble
        full_prompt = PREAMBLE[self.model_config['model']]
        if system_prompt:
            full_prompt += f"\n{system_prompt}"
        full_prompt += f"\n{prompt}"
        
        try:
            # Run async generation in sync context
            loop = asyncio.get_event_loop()
            response = loop.run_until_complete(self._generate_async(full_prompt))
            return response
            
        except Exception as e:
            raise Exception(f"NovelAI API error: {str(e)}")
    
    async def _generate_async(self, prompt: str) -> str:
        """Async implementation of text generation.
        
        Args:
            prompt: Full prompt text
            
        Returns:
            Generated text response
        """
        async with self.api_handler as api:
            response = await api.high_level.generate(
                prompt,
                self.model_config['model'],
                self.preset,
                self.global_settings,
                bad_words=self.bad_words,
                biases=self.bias_groups,
                prefix=self.module,
                stop_sequences=self.stop_sequence
            )
            
            # Decode response
            tokens = NovelAIProvider.b64_to_tokens(
                response["output"],
                self.model_config['bytes_per_token']
            )
            return NovelAIProvider.Tokenizer.decode(self.model_config['model'], tokens)
