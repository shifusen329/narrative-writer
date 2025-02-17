"""Conversation Processor Module

This module handles the processing of conversations and generation of narratives.
"""

from typing import List, Dict, Any
import json

from ..llm.providers import get_provider
from ..llm.token_counter import TokenCounter
from ..utils.file_handler import FileHandler
from .chunking import ConversationChunker

class ConversationProcessor:
    """Processes conversations and generates narratives."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the conversation processor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.llm = get_provider(config['llm'])
        self.token_counter = TokenCounter(config['llm'])
        self.chunker = ConversationChunker(config)
        
    def _create_narrative_prompt(self, chunk: Dict[str, Any], is_first_chunk: bool, is_last_chunk: bool) -> str:
        """Create a prompt for narrative generation.
        
        Args:
            chunk: Conversation chunk to process
            is_first_chunk: Whether this is the first chunk
            is_last_chunk: Whether this is the last chunk
            
        Returns:
            Formatted prompt for the LLM
        """
        # Format context and current exchanges
        context_text = ""
        if chunk['context']:
            context_exchanges = [
                f"Previous context:\n" +
                "\n".join([
                    f"Character: {exchange['prompt']}\n"
                    f"Scene: {exchange['response']}\n"
                    for exchange in chunk['context']
                ])
            ]
            context_text = "\n".join(context_exchanges)
        
        current_exchanges = [
            f"Character: {exchange['prompt']}\n"
            f"Scene: {exchange['response']}\n"
            for exchange in chunk['exchanges']
        ]
        
        # Create the prompt
        # Determine start and end instructions based on chunk position
        start_instruction = "Begin the story naturally" if is_first_chunk else "Continue the narrative seamlessly from the previous section"
        end_instruction = "Conclude the story appropriately" if is_last_chunk else "Lead naturally into the next section"
        
        prompt = (
            f"Convert the following roleplay conversation into a first-person narrative story.\n"
            f"Maintain the character's perspective, emotions, and voice throughout the narrative.\n\n"
            f"{context_text}\n\n"
            f"Current scene:\n"
            f"{chr(10).join(current_exchanges)}\n\n"
            f"Guidelines:\n"
            f"1. Write in first-person perspective\n"
            f"2. Show don't tell - use descriptive language\n"
            f"3. Maintain the emotional depth and character voice\n"
            f"4. Include all important details from the conversation\n"
            f"5. Preserve the pacing and tension\n"
            f"6. {start_instruction}\n"
            f"7. {end_instruction}"
        )

        return prompt
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for narrative generation.
        
        Returns:
            System prompt string
        """
        return """You are a skilled narrative writer converting roleplay conversations into engaging first-person stories.
Your task is to maintain the character's voice and perspective while transforming dialogue and scene descriptions 
into flowing narrative prose. Focus on showing rather than telling, and ensure all important details and emotional 
moments are preserved."""
    
    def process_conversation(self, input_file: str, output_file: str) -> None:
        """Process a conversation file and generate a narrative.
        
        Args:
            input_file: Path to input JSON conversation file
            output_file: Path to save the generated narrative
            
        Raises:
            FileNotFoundError: If input file doesn't exist
            ValueError: If conversation format is invalid
        """
        # Load conversation
        conversation = FileHandler.load_json(input_file)
        if not isinstance(conversation, list):
            raise ValueError("Invalid conversation format: expected list of exchanges")
        
        # Check if conversation fits in one chunk
        if self.token_counter.will_fit_in_context(json.dumps(conversation)):
            # Process entire conversation at once
            prompt = self._create_narrative_prompt(
                {'exchanges': conversation, 'context': []},
                is_first_chunk=True,
                is_last_chunk=True
            )
            
            # Count input tokens
            input_tokens = self.token_counter.count_tokens(prompt)
            
            # Generate narrative
            narrative = self.llm.generate(prompt, self._get_system_prompt())
            
            # Count output tokens and update totals
            output_tokens = self.token_counter.count_tokens(narrative)
            self.token_counter.add_usage(input_tokens, output_tokens)
            
            # Show usage
            model_info = f"{self.config['llm'].get('provider', 'unknown').title()} {self.config['llm'].get('model_version', 'unknown')}"
            usage = self.token_counter.get_cumulative_usage()
            print(f"\nToken usage for {model_info}:")
            print(f"  Input:  {usage['total_input_tokens']:,} tokens")
            print(f"  Output: {usage['total_output_tokens']:,} tokens")
            print(f"  Total:  {usage['total_tokens']:,} tokens")
            print(f"  Cost:   {usage['cost']}")
        else:
            # Process chunks and track token usage
            chunks = self.chunker.chunk_conversation(conversation)
            narrative_parts = []
            
            model_info = f"{self.config['llm'].get('provider', 'unknown').title()} {self.config['llm'].get('model_version', 'unknown')}"
            print(f"\nProcessing {len(chunks)} chunks using {model_info}:")
            
            # Process each chunk
            for i, chunk in enumerate(chunks):
                print(f"\nChunk {i+1}/{len(chunks)}...")
                
                # Count input tokens
                prompt = self._create_narrative_prompt(
                    chunk,
                    is_first_chunk=(i == 0),
                    is_last_chunk=(i == len(chunks) - 1)
                )
                input_tokens = self.token_counter.count_tokens(prompt)
                
                # Generate narrative
                narrative_part = self.llm.generate(prompt, self._get_system_prompt())
                narrative_parts.append(narrative_part)
                
                # Count output tokens and update totals
                output_tokens = self.token_counter.count_tokens(narrative_part)
                usage = self.token_counter.add_usage(input_tokens, output_tokens)
                
                # Show chunk usage
                chunk_stats = usage['chunk']
                print(f"\nCurrent chunk:")
                print(f"  Input:  {chunk_stats['input_tokens']:,} tokens")
                print(f"  Output: {chunk_stats['output_tokens']:,} tokens")
                print(f"  Total:  {chunk_stats['total_tokens']:,} tokens")
                print(f"  Context: {chunk_stats['context_percent']:.1f}% of window")
                
                # Show running totals
                running = usage['running']
                context = running['context_info']
                print(f"\nRunning totals:")
                print(f"  Input:  {running['input_tokens']:,} tokens")
                print(f"  Output: {running['output_tokens']:,} tokens")
                print(f"  Total:  {running['total_tokens']:,} tokens")
                print(f"  Cost:   {running['cost']}")
                
                # Warn if approaching context limits
                if context['max_percent'] > 80:
                    print(f"\nWarning: Used {context['max_percent']:.1f}% of context window")
                    print(f"Peak usage: {context['max_used']:,} tokens at total token {context['at_tokens']:,}")
        
        # Save narrative
        FileHandler.save_narrative(narrative, output_file)
