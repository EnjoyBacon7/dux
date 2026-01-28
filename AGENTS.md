# AGENTS.md - Dux Repository Guidelines

This document provides instructions for coding agents working in the Dux repository.

## Project Overview

Dux is an AI-powered job search and matching platform with:
- **Backend**: Python 3.12+ with FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: React 19 with TypeScript 5.9, Vite, Playwright
- **Documentation**: Docusaurus 3.9 with i18n support

## Build, Lint & Test Commands

### Backend (Python)

```bash
# Install dependencies
pip install -e .

# Run all tests
pytest

# Run a single test file
pytest server/test_auth_api.py

# Run a single test function
pytest server/test_auth_api.py::test_passkey_registration

# Run tests with verbose output
pytest -v

# Run tests with coverage
pytest --cov=server

# Type checking (if using mypy)
mypy server/

# Format code (if using black)
black server/

# Lint (if using ruff)
ruff check server/
```

### Frontend (TypeScript/React)

```bash
# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build

# Linting
npm run lint

# Run all E2E tests
npm test

# Run single test file
npm test -- tests/auth.spec.ts

# Run tests with UI
npm run test:ui

# Run tests headed (see browser)
npm run test:headed

# Run tests in debug mode
npm run test:debug
```

### Database

```bash
# Start PostgreSQL container
docker-compose up db -d

# Run migrations
alembic upgrade head

# Create migration
alembic revision --autogenerate -m "Migration message"

# Rollback last migration
alembic downgrade -1
```

## Code Style Guidelines

### Python (Backend)

**Imports:**
- Use absolute imports from the `server` package
- Group imports: stdlib, third-party, local (PEP 8)
- Example: `from server.models import User`

**Naming Conventions:**
- Functions: `snake_case` - e.g., `extract_cv_text()`, `validate_user_email()`
- Classes: `PascalCase` - e.g., `User`, `CVAnalyzer`
- Constants: `UPPER_SNAKE_CASE` - e.g., `MAX_FILE_SIZE`, `DEFAULT_TIMEOUT`
- Private methods: prefix with `_` - e.g., `_internal_helper()`

**Type Hints:**
- Use Pydantic models for request/response validation (required in FastAPI)
- Example: `def get_user(user_id: int) -> User:` with `User` as Pydantic BaseModel
- Use `Optional[T]` for nullable fields, `list[T]` for collections

**Error Handling:**
- Use FastAPI HTTPException for API errors: `raise HTTPException(status_code=400, detail="...")`
- Catch specific exceptions, not bare `except:`
- Log errors with context before raising: `logger.error(f"Failed to process {item_id}")`

**Database & ORM:**
- Use SQLAlchemy ORM patterns (not raw SQL)
- Define models in `server/models.py`
- Use dependency injection for database sessions: `def route(db: Session = Depends(get_db_session))`

**Authentication:**
- Passkey (WebAuthn) is preferred over password auth
- Password hashing uses Argon2 via `passlib`
- All auth routes in `server/auth_api.py`

### TypeScript/React (Frontend)

**Imports:**
- Absolute imports from `src` (configured in tsconfig)
- Group: React, libraries, components, utils, contexts
- Example: `import { useAuth } from '@/contexts/AuthContext'`

**Naming Conventions:**
- Components: `PascalCase` files and exports - e.g., `AccountCard.tsx`, `JobSearch.tsx`
- Hooks: `camelCase` - e.g., `useAuth.ts`, `useLanguage.ts`
- Constants: `UPPER_SNAKE_CASE` - e.g., `API_BASE_URL`, `LANGUAGES`
- State variables: `camelCase` - e.g., `const [isLoading, setIsLoading]`

**Type Safety:**
- Use TypeScript types, avoid `any`
- Define interfaces for props - e.g., `interface JobCardProps { ... }`
- Use React Context API for global state (AuthContext, LanguageContext)

**Formatting:**
- ESLint enforces code quality (configured in `eslint.config.js`)
- Run `npm run lint` before committing
- Indentation: 2 spaces (standard React/TypeScript)

**Component Structure:**
- Functional components with hooks (no class components)
- Place component styles in adjacent CSS Module files (e.g., `Component.module.css`)
- Import CSS modules as objects: `import styles from './Component.module.css'`
- Use scoped classNames: `className={styles['component-class']}`
- Export components at bottom of file
- Example component path: `dux-front/src/components/JobDetail.tsx`

**Testing:**
- Use Playwright for E2E tests (in `dux-front/tests/`)
- Naming convention: `feature.spec.ts` - e.g., `auth.spec.ts`, `upload.spec.ts`
- Test structure: `test.describe()` blocks with `test()` cases
- Use accessibility selectors: `page.getByRole()`, `page.getByPlaceholder()` preferred

**Routing:**
- Use React Router v7 (see `dux-front/src/` for page components)
- Routes defined in `App.tsx`
- Page components in root of `src/`: `Home.tsx`, `AuthPage.tsx`, `ProfileHub.tsx`

## Key Directories

```
dux/
├── server/                 # FastAPI backend
│   ├── app.py             # App initialization & middleware
│   ├── auth_api.py        # Authentication endpoints
│   ├── api.py             # Main router
│   ├── models.py          # SQLAlchemy ORM models
│   ├── database.py        # DB connection & session
│   ├── config.py          # Configuration (Pydantic Settings)
│   ├── routers/           # Route handlers (chat, cv, jobs, etc.)
│   ├── methods/           # Business logic (auth, upload, matching)
│   ├── cv/                # CV processing pipeline
│   ├── prompts/           # LLM prompt templates
│   ├── utils/             # Utilities (LLM clients, deps, cleanup)
│   └── test_auth_api.py   # Tests
├── dux-front/             # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── contexts/      # Context API (Auth, Language)
│   │   ├── pages/         # Page components (routed)
│   │   ├── App.tsx        # Main app
│   │   └── main.tsx       # Entry point
│   ├── tests/             # Playwright E2E tests
│   ├── package.json       # npm dependencies
│   └── eslint.config.js   # Linting rules
└── dux-docs/              # Docusaurus documentation
```

## Important Conventions

**Git Commits:**
- Use clear, descriptive commit messages
- Format: `[type]: Brief description` (e.g., `[feat]: Add CV matching algorithm`)
- Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

**Environment Variables:**
- Backend config uses Pydantic Settings (`server/config.py`)
- Load from `.env` file via `python-dotenv`
- Key vars: `DATABASE_URL`, `SESSION_SECRET`, `OPENAI_API_KEY`, `CORS_ORIGINS`

**API Endpoints:**
- All routes defined in `server/app.py` and routers
- Authentication endpoints in `server/auth_api.py`
- Use FastAPI dependency injection for DB sessions and auth

**Database:**
- PostgreSQL 16 (via docker-compose)
- Migrations via Alembic
- ORM: SQLAlchemy 2.0+

**Documentation:**
- Generate from docstrings (Python) and comments (TypeScript)
- Docusaurus site in `dux-docs/` with i18n (EN, ES, FR, DE, PT, LA)
