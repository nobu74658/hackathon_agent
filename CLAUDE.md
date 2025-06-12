# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Sales Growth AI Agent system for supporting new sales representatives through 1-on-1 analysis and action plan generation. The project consists of:

**Backend FastAPI Service** (`backend/`) - Production-ready API service with comprehensive architecture
**Slack Integration** - Real-time AI agent accessible via Slack messaging

## Development Commands

### Backend Service (FastAPI)
```bash
cd backend

# Environment setup
uv venv
source .venv/bin/activate  # macOS/Linux
uv pip install -e ".[dev]"

# Development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Code quality
black app tests          # Format code
ruff check app tests     # Lint
mypy app                 # Type check
pytest                   # Run tests
pytest --cov=app tests/  # Coverage

# Database operations
alembic upgrade head                    # Run migrations
python scripts/seed_knowledge_base.py  # Populate knowledge base with sample data
```


### Quick Demo
```bash
cd backend
python demo_script.py  # Run demonstration script
python slack_demo.py   # Test Slack integration
python slack_setup_guide.py  # Slack setup guide
```

## Architecture

### Backend Service Structure
- **FastAPI Application**: Main API service with CORS, health checks, and dependency management
- **Service Layer**: `app/services/` contains core business logic including:
  - `conversation_memory.py`: Memory management for dialogue sessions
  - `dialogue_manager.py`: AI-driven conversation flow control  
  - `real_llm_service.py`: Production LLM integration (OpenAI/Anthropic)
  - `mock_llm_service.py`: Mock service for testing without API calls
  - `slack_service.py`: Slack Bot integration and event handling
- **API Endpoints**: 
  - `app/api/test_endpoints.py`: Basic testing and health endpoints
  - `app/api/llm_demo_endpoints.py`: AI dialogue demonstration endpoints
  - `app/api/slack_endpoints.py`: Slack Events API and webhook endpoints
- **Configuration**: `app/core/config.py` handles environment variables and settings


### LLM Integration
The system supports multiple LLM providers through an abstraction layer:
- OpenAI GPT models (primary)
- Anthropic Claude models
- Mock service for development/testing

### Key Data Flow
1. User inputs 1-on-1 session text
2. AI analyzes text and extracts improvement points
3. System generates targeted questions for each improvement area
4. Interactive dialogue refines understanding
5. Comprehensive action plan generated with specific, measurable goals

## Environment Configuration

### Required Environment Variables
```bash
# LLM Configuration
USE_MOCK_LLM=false              # Set to true for testing without API calls
OPENAI_API_KEY=your-key-here    # Required if using OpenAI
ANTHROPIC_API_KEY=your-key-here # Required if using Anthropic

# Slack Integration
SLACK_BOT_TOKEN=xoxb-your-token # Bot User OAuth Token
SLACK_SIGNING_SECRET=your-secret # App Signing Secret
SLACK_APP_TOKEN=xapp-your-token # App-Level Token (Socket Mode)

# API Configuration  
CORS_ORIGINS=*                  # Configure for production
LOG_LEVEL=INFO
DEBUG=true                      # Development only
```

## Testing Strategy

- **Unit Tests**: Located in `backend/tests/` and `backend/test_basic.py`
- **Mock Services**: Use `USE_MOCK_LLM=true` for API-free testing
- **Integration**: Demo script provides end-to-end testing workflow
- **Coverage**: Target 90%+ test coverage with pytest-cov

## Key Technical Considerations

- All LLM calls are asynchronous for better performance
- Conversation context is maintained in memory services
- Error handling includes graceful degradation for LLM API failures  
- Both Japanese and English content supported in prompts and responses
- Database operations use proper connection pooling and async patterns
- Slack integration supports DMs, channel mentions, and session management per user