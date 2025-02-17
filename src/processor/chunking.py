"""Chunking Module

This module handles the chunking of conversations into manageable segments while preserving context.
"""

from typing import List, Dict, Any, Tuple
import re

class ConversationChunker:
    """Handles chunking of conversations into processable segments."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the chunker with configuration.
        
        Args:
            config: Configuration dictionary containing chunking parameters
        """
        self.split_on_scenes = config.get('processing', {}).get('split_on_scene_changes', True)
        self.context_exchanges = config.get('processing', {}).get('context_exchanges', 2)
    
    def detect_scene_change(self, current: Dict[str, str], next_exchange: Dict[str, str]) -> bool:
        """Detect if there's a significant scene change between exchanges.
        
        Args:
            current: Current conversation exchange
            next_exchange: Next conversation exchange
            
        Returns:
            True if a scene change is detected
        """
        # Common scene change indicators
        indicators = [
            r"later",
            r"the next day",
            r"after [^.]*",
            r"suddenly",
            r"meanwhile",
            r"elsewhere",
            r"hours? (later|passed)",
            r"days? (later|passed)",
            r"the following",
            r"that (evening|morning|afternoon|night)",
        ]
        
        pattern = '|'.join(f"\\b{i}\\b" for i in indicators)
        
        # Check both prompt and response for scene change indicators
        next_text = f"{next_exchange['prompt']} {next_exchange['response']}"
        return bool(re.search(pattern, next_text, re.IGNORECASE))
    
    def find_chunk_boundaries(self, conversation: List[Dict[str, str]]) -> List[Tuple[int, int]]:
        """Find optimal chunk boundaries in the conversation.
        
        Args:
            conversation: List of conversation exchanges
            
        Returns:
            List of (start_idx, end_idx) tuples defining chunks
        """
        chunks = []
        current_start = 0
        
        for i in range(1, len(conversation)):
            # Check for scene changes if enabled
            if self.split_on_scenes and i < len(conversation) - 1:
                if self.detect_scene_change(conversation[i], conversation[i + 1]):
                    chunks.append((current_start, i + 1))
                    current_start = i + 1
                    continue
        
        # Add the final chunk
        if current_start < len(conversation):
            chunks.append((current_start, len(conversation)))
        
        return chunks
    
    def get_context_for_chunk(self, conversation: List[Dict[str, str]], 
                            start_idx: int, previous_chunk_end: int = None) -> List[Dict[str, str]]:
        """Get relevant context exchanges for a chunk.
        
        Args:
            conversation: Full conversation list
            start_idx: Start index of current chunk
            previous_chunk_end: End index of previous chunk
            
        Returns:
            List of context exchanges
        """
        if previous_chunk_end is None or start_idx == 0:
            return []
        
        # Get the specified number of exchanges before this chunk
        context_start = max(previous_chunk_end - self.context_exchanges, 0)
        context = conversation[context_start:previous_chunk_end]
        
        return context
    
    def chunk_conversation(self, conversation: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Split conversation into chunks with context.
        
        Args:
            conversation: List of conversation exchanges
            
        Returns:
            List of chunks, each containing:
                - exchanges: List of conversation exchanges for this chunk
                - context: List of relevant context exchanges from previous chunk
        """
        chunk_boundaries = self.find_chunk_boundaries(conversation)
        chunks = []
        previous_end = None
        
        for start, end in chunk_boundaries:
            chunk = {
                'exchanges': conversation[start:end],
                'context': self.get_context_for_chunk(conversation, start, previous_end)
            }
            chunks.append(chunk)
            previous_end = end
        
        return chunks
