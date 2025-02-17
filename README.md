# Narrative Writer

A CLI tool for converting roleplay conversations into narrative stories using various LLM providers.

## Features
- Multiple LLM providers:
  - OpenAI (GPT-4o, GPT-4o-mini)
  - Anthropic (Claude 3 Opus/Sonnet/Haiku)
  - Google (Gemini 2.0/1.5 Flash, 1.5 Pro)
  - NovelAI (Erato, Kayra, Clio, Krake)
- Smart conversation chunking with context preservation
- Token usage tracking and cost estimation
- Provider-specific optimizations
- Configurable narrative styles

## Installation

```bash
# Clone repository
git clone [repository-url]
cd narrative-writer

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

## Usage

```bash
# Basic usage with default model (GPT-4o)
python narrative_writer.py input.json output.txt

# Use specific model
python narrative_writer.py input.json output.txt --model erato

# Use custom config
python narrative_writer.py input.json output.txt --config custom_config.json
```

### Input Format

Input files should be JSON arrays of conversation exchanges:

```json
[
  {
    "prompt": "Character's action/dialogue",
    "response": "Scene description/response"
  },
  {
    "prompt": "I look around the dimly lit tavern, searching for familiar faces.",
    "response": "The tavern is sparsely populated at this hour. A few regulars huddle over their drinks in the corners, while a bard quietly tunes his lute by the hearth."
  }
]
```

### Configuration

The tool can be configured through `config.json`:

```json
{
  "llm": {
    "provider": "openai",
    "model_version": "gpt-4o",
    "temperature": 0.7
  },
  "processing": {
    "split_on_scene_changes": true,
    "context_exchanges": 2,
    "style": "first_person_narrative"
  }
}
```

See `docs/model_comparison.md` for detailed provider information and pricing.

## Features in Detail

### Smart Chunking
- Automatically splits long conversations into optimal chunks
- Preserves context between chunks for coherent narratives
- Handles scene transitions smoothly

### Token Management
- Tracks token usage across chunks
- Provides per-chunk and cumulative usage statistics
- Estimates costs for pay-per-token providers
- Supports subscription-based providers

### Provider Support
- OpenAI: Latest GPT-4 models with 128k context
- Anthropic: Claude 3 series with 200k context
- Google: Gemini models with up to 2M context
- NovelAI: Specialized storytelling models

## Development

### Project Structure
```
narrative-writer/
├── config.json           # Configuration file
├── .env                 # API keys
├── src/
│   ├── llm/            # LLM provider implementations
│   ├── processor/      # Conversation processing
│   └── utils/          # Helper utilities
└── docs/
    └── model_comparison.md  # Provider details
```

### Running Tests
```bash
pytest tests/
```

## License

MIT License - See LICENSE file for details.
