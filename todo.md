# Narrative Writer Implementation Plan

## Project Structure
```
narrative-writer/
├── config.json           # Configuration file
├── .env                  # API keys (already exists)
├── src/
│   ├── __init__.py
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── provider.py      # LLM provider implementations
│   │   └── token_counter.py # Token counting utilities
│   ├── processor/
│   │   ├── __init__.py
│   │   ├── conversation.py  # Conversation processing
│   │   └── chunking.py      # Chunking strategies
│   └── utils/
│       ├── __init__.py
│       └── file_handler.py  # JSON/file operations
└── tests/
    └── ...               # Test files for each module
```

## Implementation Steps

### 1. Project Setup
- [x] Create directory structure
- [x] Initialize Python package
- [x] Set up virtual environment
- [x] Install required dependencies:
  - langchain
  - python-dotenv
  - anthropic
  - openai
  - google-generativeai
  - tiktoken (for token counting)

### 2. LLM Provider Implementation
- [x] Create base LLM provider interface
- [x] Implement provider-specific classes:
  - [x] OpenAI (GPT-4o, GPT-4o-mini)
  - [x] Anthropic (Claude 3 Opus/Sonnet/Haiku)
  - [x] Google (Gemini 2.0/1.5 Flash, 1.5 Pro)
  - [x] NovelAI (Erato, Kayra, Clio, Krake)
  - [ ] Ollama
- [x] Add token counting for each provider
- [x] Add cost calculation for each provider
- [x] Implement provider selection logic
- [x] Add cumulative token tracking

### 3. Conversation Processing
- [x] Implement conversation loading from JSON
- [x] Create token estimation logic
- [x] Develop chunking strategies:
  - [x] Scene/topic change detection
  - [x] Context preservation between chunks
  - [x] Optimal chunk size calculation
- [x] Add narrative generation logic:
  - [x] Prompt engineering for first-person narrative
  - [x] Context management between chunks
  - [x] Smooth transition handling

### 4. File Handling
- [x] JSON parsing utilities
- [x] File reading/writing helpers
- [x] Configuration management
- [x] Output formatting

### 5. Testing
- [ ] Unit tests for each module
- [ ] Integration tests for full pipeline
- [ ] Test with various conversation sizes
- [ ] Validate output quality
- [ ] Performance testing

### 6. Documentation
- [x] Code documentation
- [x] Usage examples
- [x] API documentation
- [x] Configuration guide
- [x] Model comparison guide

### 7. Repository Setup
- [ ] Initialize git repository
- [ ] Create README.md
- [ ] Add .gitignore
- [ ] Create .env.example
- [ ] Prepare initial commit

## Testing Scenarios
1. Small conversations (within token limits)
2. Large conversations (requiring chunking)
3. Different LLM providers and models:
   - GPT-4-turbo (128k context)
   - GPT-3.5-turbo (16k context)
4. Various narrative styles
5. Error handling and recovery

## Configuration Options
```json
{
    "llm": {
        "provider": "anthropic",
        "model": "claude-2.1",
        "temperature": 0.7,
        "max_input_tokens": 200000
    },
    "processing": {
        "split_on_scene_changes": true,
        "context_exchanges": 2,
        "style": "first_person_narrative"
    }
}
```

Please review this implementation plan. Once approved, we can proceed with the implementation starting with the project setup and basic structure.
