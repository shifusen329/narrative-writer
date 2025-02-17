"""Token Counter Module

This module provides utilities for token counting and text chunking based on token limits.
"""

from typing import List, Dict, Any
import json

from .providers import get_provider

class TokenCounter:
    """Handles token counting and text chunking."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize TokenCounter with LLM provider.
        
        Args:
            config: LLM configuration dictionary
        """
        self.provider = get_provider(config)
        self.max_tokens = config.get('max_input_tokens', 128000)
        
        # Track cumulative token usage
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        
        # Track context window usage
        self.max_context_used = 0
        self.max_context_chunk = 0
        
    def add_usage(self, input_tokens: int, output_tokens: int) -> Dict[str, Any]:
        """Add token usage to cumulative totals.
        
        Args:
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens used
        """
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        
        # Update context window tracking
        chunk_total = input_tokens + output_tokens
        if chunk_total > self.max_context_used:
            self.max_context_used = chunk_total
            self.max_context_chunk = self.total_input_tokens + self.total_output_tokens
        
        # Calculate cost if not subscription-based
        costs = self.provider.calculate_cost(input_tokens, output_tokens)
        if 'subscription' not in costs:
            self.total_cost += costs['total_cost']
            
        # Return current chunk stats
        return {
            'chunk': {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': chunk_total,
                'context_percent': (chunk_total / self.max_tokens) * 100
            },
            'running': self.get_running_totals()
        }
    
    def get_running_totals(self) -> Dict[str, Any]:
        """Get running token totals and context usage.
        
        Returns:
            Dictionary with running totals and context info
        """
        total_tokens = self.total_input_tokens + self.total_output_tokens
        costs = self.provider.calculate_cost(
            self.total_input_tokens,
            self.total_output_tokens
        )
        
        return {
            'input_tokens': self.total_input_tokens,
            'output_tokens': self.total_output_tokens,
            'total_tokens': total_tokens,
            'cost': costs.get('subscription', f"${self.total_cost:.4f}"),
            'context_info': {
                'max_used': self.max_context_used,
                'max_allowed': self.max_tokens,
                'max_percent': (self.max_context_used / self.max_tokens) * 100,
                'at_tokens': self.max_context_chunk
            }
        }
    
    def count_conversation_tokens(self, conversation: List[Dict[str, str]]) -> int:
        """Count tokens in a conversation.
        
        Args:
            conversation: List of conversation exchanges
                        [{"prompt": "...", "response": "..."}, ...]
            
        Returns:
            Total number of tokens in the conversation
        """
        # Convert conversation to string for token counting
        conversation_text = json.dumps(conversation)
        return self.provider.count_tokens(conversation_text)
    
    def estimate_chunks_needed(self, total_tokens: int) -> int:
        """Estimate number of chunks needed based on token count.
        
        Args:
            total_tokens: Total number of tokens in the text
            
        Returns:
            Number of chunks needed
        """
        # Leave room for system prompt and generation
        effective_limit = int(self.max_tokens * 0.8)
        return (total_tokens + effective_limit - 1) // effective_limit
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using provider's counter.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens in the text
        """
        return self.provider.count_tokens(text)
    
    def will_fit_in_context(self, text: str) -> bool:
        """Check if text will fit within token limit.
        
        Args:
            text: Text to check
            
        Returns:
            True if text fits within token limit, False otherwise
        """
        token_count = self.provider.count_tokens(text)
        # Leave room for system prompt and generation
        return token_count <= int(self.max_tokens * 0.8)
