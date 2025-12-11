# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MUDS学生マッチングシステム - A student matching system for Musashino University Data Science Department. Matches juniors (questioners) with seniors (answerers) using TF-IDF and cosine similarity algorithms, with Slack notification integration.

## Development Commands

### Backend (Python/FastAPI)

```bash
# Setup virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the development server (with auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Alternative: Run directly
python -m app.main

# Run tests
pytest
pytest --cov=app  # with coverage
pytest tests/test_specific.py  # single test file

# Code quality
black .                    # format code
flake8                     # lint
mypy app                   # type checking

# Database migrations
alembic revision --autogenerate -m "description"  # create migration
alembic upgrade head                              # apply migrations
alembic downgrade -1                              # rollback one migration
alembic history                                   # view migration history
```

### Frontend (React/TypeScript/Vite)

```bash
cd dashboard

# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build

# Lint
npm run lint

# Preview production build
npm run preview
```

## Architecture

### High-Level System Flow

1. **Data Sync**: Google Sheets form responses → FastAPI endpoints → SQLite database
2. **Matching Algorithm**: TF-IDF vectorization → Cosine similarity calculation → Top 3 seniors selected
3. **Notification**: Slack Bot sends DMs to selected seniors → First-come first-served acceptance
4. **Exclusion Control**: Multiple seniors can respond, but only the first acceptance is processed

### Backend Structure (`app/`)

**Entry Point**: `app/main.py` - FastAPI application with CORS, logging setup, and lifespan management

**Data Models** (`models.py`):
- `Junior`: Questioner profile with consultation details
- `Senior`: Answerer profile with available areas and availability status
- `Matching`: Matching history with status tracking (pending/accepted/completed/cancelled)

**Core Services** (`services/`):
- `sheets_service.py`: Google Sheets API integration for syncing form responses
- `matching_service.py`: TF-IDF + cosine similarity matching algorithm
  - Uses MeCab for Japanese tokenization (falls back to character n-grams)
  - Scoring: 60% similarity + 20% availability + 20% matching history
- `slack_service.py`: Slack Bot integration for sending notifications and handling responses

**API Endpoints** (`api/`):
- `sync.py`: Admin-only endpoints for syncing juniors/seniors from Google Sheets
  - Requires `X-Admin-Token` header matching `ADMIN_API_KEY` env var
- `matchings.py`: Matching creation and management endpoints
  - `/create`: Auto-match junior with top 3 seniors, send Slack notifications
  - `/accept`: Senior accepts a matching (first-come first-served)
  - Status transitions: pending → accepted → completed

**Database**:
- SQLite with SQLAlchemy ORM
- Alembic for migrations
- Database file location: `data/students_matching.db`

### Frontend Structure (`dashboard/`)

React + TypeScript + Vite application (currently basic setup)

### Environment Configuration

Required environment variables (`.env`):
- `ADMIN_API_KEY`: Admin token for protected endpoints
- Google Sheets API credentials
- Slack Bot tokens and signing secrets
- Database URL (defaults to SQLite)

### Key Design Patterns

**Exclusion Control**: Matching status ensures only one senior can accept each junior's request. The first senior to call `/accept` wins.

**Matching Algorithm**:
1. Extract junior's consultation content (title + content + category + phases)
2. Extract senior's available areas (interest areas + categories + research phases)
3. TF-IDF vectorize both texts
4. Calculate cosine similarity (0.0-1.0)
5. Apply scoring formula with availability and history weights
6. Select top 3 seniors

**Slack Integration**: Uses Slack SDK to send DMs and handle interactive components. Stores `slack_user_id` in both Junior and Senior tables for direct messaging.

## Testing Files

- `test_sync.py`: Tests for Google Sheets sync functionality
- `test_sync_update.py`: Tests for update operations
- `generate_dummy_data.py`: Utility to generate test data

## Database Schema

All models include:
- Timestamps: `created_at`, `updated_at`
- Constraints: Email format validation, student ID length (7 digits), enum values
- Indexes: On frequently queried fields (student_id, is_matched, availability_status, etc.)

## Important Notes

- Student IDs must be exactly 7 digits
- Junior emails must end with `@stu.musashino-u.ac.jp`
- Matching scores are calculated using TF-IDF + cosine similarity
- Seniors have availability status (0-2) and optional unavailable date ranges
- All API endpoints use `/api/v1/` prefix
- Protected endpoints require `X-Admin-Token` header
