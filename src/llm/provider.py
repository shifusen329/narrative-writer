"""LLM Provider Module

This module defines the base LLM provider interface and implements provider-specific classes.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
import os

import tiktoken
from openai import OpenAI
import anthropic
import google.generativeai as genai

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the LLM provider with configuration.
        
        Args:
            config: Dictionary containing provider configuration
                   (model, temperature, max_tokens, etc.)
        """
        self.config = config
        self.model = config.get('model')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_input_tokens', 128000)
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in the input text.
        
        Args:
            text: Input text to count tokens for
            
        Returns:
            Number of tokens in the text
        """
        pass
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text using the LLM.
        
        Args:
            prompt: The main prompt text
            system_prompt: Optional system prompt for models that support it
            
        Returns:
            Generated text response
        """
        pass
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> Dict[str, float]:
        """Calculate cost for token usage.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Dictionary containing input_cost, output_cost, and total_cost
        """
        pass

class OpenAIProvider(LLMProvider):
    """OpenAI-specific LLM provider implementation."""
    
    MODEL_CONFIGS = {
        "gpt-4o": {
            "model": "gpt-4o-2024-08-06",
            "max_input_tokens": 128000,
            "max_output_tokens": 4096,
            "input_price": 0.0025,   # $2.50 per 1M tokens
            "output_price": 0.01,    # $10.00 per 1M tokens
        },
        "gpt-4o-mini": {
            "model": "gpt-4o-mini-2024-07-18",
            "max_input_tokens": 128000,
            "max_output_tokens": 4096,
            "input_price": 0.00015,  # $0.15 per 1M tokens
            "output_price": 0.0006   # $0.60 per 1M tokens
        }
    }
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize OpenAI provider.
        
        Args:
            config: OpenAI-specific configuration
            
        Raises:
            ValueError: If model_version is invalid
        """
        # Get model configuration based on version
        model_version = config.get('model_version', 'gpt-4o')
        if model_version not in self.MODEL_CONFIGS:
            raise ValueError(f"Invalid model version: {model_version}. Must be one of {list(self.MODEL_CONFIGS.keys())}")
            
        model_config = self.MODEL_CONFIGS[model_version]
        
        # Update config with model-specific settings
        config['model'] = model_config['model']
        config['max_input_tokens'] = model_config['max_input_tokens']
        
        super().__init__(config)
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.encoding = tiktoken.encoding_for_model(self.model)
        self.model_config = model_config
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken for OpenAI models.
        
        Args:
            text: Input text to count tokens for
            
        Returns:
            Number of tokens in the text
        """
        return len(self.encoding.encode(text))
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> Dict[str, float]:
        """Calculate cost for OpenAI token usage.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Dictionary containing input_cost, output_cost, and total_cost
        """
        input_cost = (input_tokens / 1_000_000) * self.model_config['input_price']
        output_cost = (output_tokens / 1_000_000) * self.model_config['output_price']
        total_cost = input_cost + output_cost
        
        return {
            'input_cost': input_cost,
            'output_cost': output_cost,
            'total_cost': total_cost
        }
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text using OpenAI's chat completion API.
        
        Args:
            prompt: The main prompt text
            system_prompt: Optional system instructions
            
        Returns:
            Generated text response
            
        Raises:
            Exception: If the API call fails
        """
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
            
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        try:
            # Count input tokens
            input_text = "\n".join([m["content"] for m in messages])
            input_tokens = self.count_tokens(input_text)
            
            # Make API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.model_config['max_output_tokens']
            )
            
            # Count output tokens and calculate cost
            output_text = response.choices[0].message.content
            return output_text
            
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

class AnthropicProvider(LLMProvider):
    """Anthropic-specific LLM provider implementation."""
    
    MODEL_CONFIGS = {
        "claude-3-opus-latest": {
            "model": "claude-3-opus-20240229",
            "max_input_tokens": 200000,
            "max_output_tokens": 4096,
            "input_price": 0.015,    # $15.00 per 1M tokens
            "output_price": 0.075    # $75.00 per 1M tokens
        },
        "claude-3-sonnet-latest": {
            "model": "claude-3-sonnet-20240229",
            "max_input_tokens": 200000,
            "max_output_tokens": 4096,
            "input_price": 0.003,    # $3.00 per 1M tokens
            "output_price": 0.015    # $15.00 per 1M tokens
        },
        "claude-3-haiku-latest": {
            "model": "claude-3-haiku-20240229",
            "max_input_tokens": 200000,
            "max_output_tokens": 4096,
            "input_price": 0.0008,   # $0.80 per 1M tokens
            "output_price": 0.004    # $4.00 per 1M tokens
        }
    }
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Anthropic provider.
        
        Args:
            config: Anthropic-specific configuration
            
        Raises:
            ValueError: If model_version is invalid
        """
        model_version = config.get('model_version', 'claude-3-opus-latest')
        if model_version not in self.MODEL_CONFIGS:
            raise ValueError(f"Invalid model version: {model_version}. Must be one of {list(self.MODEL_CONFIGS.keys())}")
            
        model_config = self.MODEL_CONFIGS[model_version]
        
        config['model'] = model_config['model']
        config['max_input_tokens'] = model_config['max_input_tokens']
        
        super().__init__(config)
        self.client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.model_config = model_config
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using Anthropic's token counter.
        
        Args:
            text: Input text to count tokens for
            
        Returns:
            Number of tokens in the text
        """
        return self.client.count_tokens(text)
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> Dict[str, float]:
        """Calculate cost for Anthropic token usage.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Dictionary containing input_cost, output_cost, and total_cost
        """
        input_cost = (input_tokens / 1_000_000) * self.model_config['input_price']
        output_cost = (output_tokens / 1_000_000) * self.model_config['output_price']
        total_cost = input_cost + output_cost
        
        return {
            'input_cost': input_cost,
            'output_cost': output_cost,
            'total_cost': total_cost
        }
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text using Anthropic's API.
        
        Args:
            prompt: The main prompt text
            system_prompt: Optional system instructions
            
        Returns:
            Generated text response
            
        Raises:
            Exception: If the API call fails
        """
        try:
            # Count input tokens
            input_text = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            input_tokens = self.count_tokens(input_text)
            
            # Make API call
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.model_config['max_output_tokens'],
                temperature=self.temperature,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Get output text
            output_text = message.content[0].text
            return output_text
            
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")

class GeminiProvider(LLMProvider):
    """Google's Gemini-specific LLM provider implementation."""
    
    MODEL_CONFIGS = {
        "gemini-2.0-flash": {
            "model": "gemini-2.0-flash",
            "max_input_tokens": 1000000,  # 1M token context
            "max_output_tokens": 4096,
            "input_price": 0.0001,   # $0.10 per 1M tokens
            "output_price": 0.0004   # $0.40 per 1M tokens
        },
        "gemini-1.5-flash": {
            "model": "gemini-1.5-flash",
            "max_input_tokens": 1000000,  # 1M token context
            "max_output_tokens": 4096,
            "input_price": {
                "standard": 0.000075,  # $0.075 per 1M tokens (≤128k)
                "extended": 0.00015    # $0.15 per 1M tokens (>128k)
            },
            "output_price": {
                "standard": 0.0003,    # $0.30 per 1M tokens (≤128k)
                "extended": 0.0006     # $0.60 per 1M tokens (>128k)
            }
        },
        "gemini-1.5-pro": {
            "model": "gemini-1.5-pro",
            "max_input_tokens": 2000000,  # 2M token context
            "max_output_tokens": 4096,
            "input_price": {
                "standard": 0.00125,   # $1.25 per 1M tokens (≤128k)
                "extended": 0.0025     # $2.50 per 1M tokens (>128k)
            },
            "output_price": {
                "standard": 0.005,     # $5.00 per 1M tokens (≤128k)
                "extended": 0.01       # $10.00 per 1M tokens (>128k)
            }
        }
    }
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Gemini provider.
        
        Args:
            config: Gemini-specific configuration
            
        Raises:
            ValueError: If model_version is invalid
        """
        model_version = config.get('model_version', 'gemini-2.0-flash')
        if model_version not in self.MODEL_CONFIGS:
            raise ValueError(f"Invalid model version: {model_version}. Must be one of {list(self.MODEL_CONFIGS.keys())}")
            
        model_config = self.MODEL_CONFIGS[model_version]
        
        config['model'] = model_config['model']
        config['max_input_tokens'] = model_config['max_input_tokens']
        
        super().__init__(config)
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel(model_config['model'])
        self.model_config = model_config
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using Gemini's token counter.
        
        Args:
            text: Input text to count tokens for
            
        Returns:
            Number of tokens in the text
        """
        return self.model.count_tokens(text).total_tokens
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> Dict[str, float]:
        """Calculate cost for Gemini token usage.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Dictionary containing input_cost, output_cost, and total_cost
        """
        # Handle fixed pricing models
        if isinstance(self.model_config['input_price'], (int, float)):
            input_cost = (input_tokens / 1_000_000) * self.model_config['input_price']
            output_cost = (output_tokens / 1_000_000) * self.model_config['output_price']
        else:
            # Handle tiered pricing models
            input_price = (
                self.model_config['input_price']['standard']
                if input_tokens <= 128000
                else self.model_config['input_price']['extended']
            )
            output_price = (
                self.model_config['output_price']['standard']
                if output_tokens <= 128000
                else self.model_config['output_price']['extended']
            )
            input_cost = (input_tokens / 1_000_000) * input_price
            output_cost = (output_tokens / 1_000_000) * output_price
        
        total_cost = input_cost + output_cost
        
        return {
            'input_cost': input_cost,
            'output_cost': output_cost,
            'total_cost': total_cost
        }
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text using Gemini's API.
        
        Args:
            prompt: The main prompt text
            system_prompt: Optional system instructions
            
        Returns:
            Generated text response
            
        Raises:
            Exception: If the API call fails
        """
        try:
            # Count input tokens
            input_text = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            input_tokens = self.count_tokens(input_text)
            
            # Make API call
            response = self.model.generate_content(
                input_text,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.model_config['max_output_tokens']
                )
            )
            
            # Get output text
            output_text = response.text
            return output_text
            
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")

# Provider registration moved to providers.py
