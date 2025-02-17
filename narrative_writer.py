#!/usr/bin/env python3
"""Narrative Writer CLI

Command-line interface for converting roleplay conversations to narrative form.
"""

import argparse
import sys
from typing import Dict, Any, List
import json

from src.utils.file_handler import FileHandler
from src.processor.conversation import ConversationProcessor

def get_pricing_info() -> str:
    """Get formatted pricing information.
    
    Returns:
        Pricing information string
    """
    return """
pricing:
  OpenAI:     Pay per token ($2.50-$10.00 per 1M tokens)
  Anthropic:  Pay per token ($0.80-$75.00 per 1M tokens)
  Gemini:     Pay per token ($0.10-$10.00 per 1M tokens)
  NovelAI:    $20/month unlimited generations

For detailed model comparison and pricing, see docs/model_comparison.md"""

def get_examples() -> str:
    """Get formatted usage examples.
    
    Returns:
        Examples string
    """
    return """
examples:
  # Generate narrative using default model (gpt-4o)
  python narrative_writer.py input.json output.txt

  # Use specific model
  python narrative_writer.py input.json output.txt --model erato

  # Use custom config
  python narrative_writer.py input.json output.txt --config custom_config.json"""

def load_available_models(config_path: str) -> Dict[str, list]:
    """Load available models from config.
    
    Args:
        config_path: Path to config file
        
    Returns:
        Dictionary of provider -> list of models
    """
    config = FileHandler.load_config(config_path)
    return config.get('available_models', {})

def get_all_models(available_models: Dict[str, List[str]]) -> List[str]:
    """Get flat list of all available models.
    
    Args:
        available_models: Dictionary of provider -> list of models
        
    Returns:
        List of all model names
    """
    all_models = []
    for provider_models in available_models.values():
        all_models.extend(provider_models)
    return all_models

def parse_args() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    # Load available models
    try:
        available_models = load_available_models('config.json')
        all_models = get_all_models(available_models)
    except:
        all_models = ['gpt-4o', 'gpt-4o-mini']  # Fallback defaults
    
    # Create parser with custom formatting
    parser = argparse.ArgumentParser(
        description='Convert roleplay conversations to narrative form',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=get_examples() + get_pricing_info(),
        usage='%(prog)s [-h] [--config CONFIG] [--model MODEL] input_file output_file'
    )
    
    parser.add_argument(
        'input_file',
        help='Path to input JSON conversation file'
    )
    
    parser.add_argument(
        'output_file',
        help='Path to save the generated narrative'
    )
    
    parser.add_argument(
        '--config',
        default='config.json',
        help='Path to configuration file (default: config.json)'
    )
    
    model_help = (
        'Model to use (default: gpt-4o)\n'
        'Available models:\n'
        '  OpenAI:    gpt-4o, gpt-4o-mini\n'
        '  Anthropic: claude-3-opus-latest, claude-3-sonnet-latest, claude-3-haiku-latest\n'
        '  Gemini:    gemini-2.0-flash, gemini-1.5-flash, gemini-1.5-pro\n'
        '  NovelAI:   erato, kayra, clio, krake'
    )
    parser.add_argument(
        '--model',
        choices=all_models,
        default='gpt-4o',
        metavar='MODEL',
        help=model_help
    )
    
    return parser.parse_args()

def get_provider_for_model(model: str, available_models: Dict[str, list]) -> str:
    """Get the provider for a given model.
    
    Args:
        model: Model name
        available_models: Dictionary of provider -> list of models
        
    Returns:
        Provider name
        
    Raises:
        ValueError: If model not found
    """
    for provider, models in available_models.items():
        if model in models:
            return provider
    raise ValueError(f"Model {model} not found in available models")

def main() -> int:
    """Main entry point.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        args = parse_args()
        
        # Load configuration
        config = FileHandler.load_config(args.config)
        available_models = config.get('available_models', {})
        
        # Override model version if specified
        if args.model:
            provider = get_provider_for_model(args.model, available_models)
            config['llm']['provider'] = provider
            config['llm']['model_version'] = args.model
        
        # Initialize processor
        processor = ConversationProcessor(config)
        
        # Process conversation
        processor.process_conversation(args.input_file, args.output_file)
        
        print(f"Successfully generated narrative: {args.output_file}")
        return 0
        
    except FileNotFoundError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON - {str(e)}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
