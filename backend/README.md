# Sales Growth AI Backend

## Setup

### Prerequisites
- Python 3.11+
- uv (Python package manager)
- PostgreSQL
- Redis

### Installation

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows

# Install dependencies
uv pip install -e ".[dev]"

# Or sync from lock file
uv pip sync
```

### Environment Setup

```bash
cp .env.example .env
# Edit .env with your configuration
```

### Database Setup

```bash
# Run migrations
alembic upgrade head
```

### Running the Server

```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Development

### Code Quality

```bash
# Format code
black app tests

# Lint
ruff check app tests

# Type check
mypy app

# Run tests
pytest

# Coverage
pytest --cov=app tests/
```