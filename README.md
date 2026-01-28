
<p align="center">
  <img src="https://github.com/EnjoyBacon7/dux/blob/main/dux-docs/static/img/dux_logo.png">
</p>
# Dux

Dux is an AI-powered job search and matching platform that helps users search, rank, and apply to jobs faster. The platform analyzes CVs, matches job opportunities to user profiles, and provides intelligent insights to streamline the job application process.

## Vision

Dux aims to simplify job searching by leveraging AI to match candidates with opportunities that align with their skills, experience, and preferences. The platform integrates with existing job databases and professional networks to provide comprehensive, ranked job recommendations with detailed match analysis.

## Tech Stack

### Backend

- **FastAPI** - Modern Python web framework for building APIs
- **SQLAlchemy** - SQL toolkit and ORM for database management
- **PostgreSQL** - Relational database for data persistence
- **Uvicorn** - ASGI server for running the FastAPI application
- **WebAuthn** - Passwordless authentication with passkeys
- **Passlib (Argon2)** - Password hashing for traditional authentication
- **PyPDF** - PDF processing for CV extraction
- **Pytesseract & Pillow** - OCR capabilities for document analysis
- **Pandas** - Data manipulation and analysis
- **Python-DOCX** - Microsoft Word document processing
- **APScheduler** - Background task scheduling for automated job matching

### Frontend

- **React 19** - UI library for building interactive interfaces
- **TypeScript** - Type-safe JavaScript development
- **Vite** - Build tool and development server
- **React Router** - Client-side routing
- **React Markdown** - Markdown rendering for job descriptions
- **Playwright** - End-to-end testing framework

### Documentation

- **Docusaurus** - Documentation site generator with internationalization support

### Infrastructure

- **Docker & Docker Compose** - Containerization and orchestration
- **PostgreSQL 16** - Database container
- **Alembic** - Database migrations

## Installation

### Prerequisites

- Docker and Docker Compose
- Node.js (for local frontend development)
- Python 3.12+ (for local backend development)

### Quick Start with Docker

1. Clone the repository:

```bash
git clone https://github.com/EnjoyBacon7/dux.git
cd dux
```

2. Set up environment variables (optional):

```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start the application:

```bash
docker-compose up
```

The application will be available at `http://localhost:8080`

### Local Development

#### Backend Setup

1. Install Python dependencies:

```bash
pip install -e .
```

2. Set up the database:

```bash
# Start PostgreSQL container
docker-compose up db -d

# Run migrations
alembic upgrade head
```

3. Start the development server:

```bash
uvicorn server.app:app --reload --host 0.0.0.0 --port 8080
```

#### Frontend Setup

1. Navigate to the frontend directory:

```bash
cd dux-front
```

2. Install dependencies:

```bash
npm install
```

3. Start the development server:

```bash
npm run dev
```

#### Documentation Setup

1. Navigate to the documentation directory:

```bash
cd dux-docs
```

2. Install dependencies:

```bash
npm install
```

3. Start the documentation server:

```bash
npm run start
```

### Environment Variables

Key environment variables for configuration:

- `DATABASE_URL` - PostgreSQL connection string
- `SESSION_SECRET` - Secret key for session management
- `CORS_ORIGINS` - Allowed CORS origins
- `RP_ID` - WebAuthn Relying Party ID
- `RP_NAME` - WebAuthn Relying Party name
- `ORIGIN` - Application origin URL

Refer to [docker-compose.yml](docker-compose.yml) for the complete list of configuration options.

## Features

- **CV Analysis** - Upload CVs in PDF or DOCX format for AI-powered analysis
- **Automated Job Recommendations** - Optimal job offers are automatically generated hourly for all users and immediately after CV upload
- **Job Search** - Advanced filtering and search across job databases
- **Profile Management** - Comprehensive user profiles with experience and skills
- **LinkedIn Integration** - OAuth integration for profile enrichment
- **Multilingual Support** - Available in English, Spanish, French, German, Portuguese, and Latin
- **Passwordless Authentication** - Modern passkey-based authentication with WebAuthn
- **Privacy-Focused** - User data ownership and transparency

## Background Tasks

The platform includes automated background tasks that run periodically to ensure users always have fresh job recommendations:

- **Hourly Job Matching** - Every hour, the system automatically generates optimal job offers for all users who have uploaded a CV
- **On-Upload Matching** - When a user uploads a new CV, the system immediately generates personalized job recommendations
- **Smart Caching** - Results are cached for one hour to optimize performance while ensuring freshnesshentication with WebAuthn

## Testing

Run frontend tests:

```bash
cd dux-front
npm test
```

Run backend tests:

```bash
pytest
```

## License

See [LICENSE](LICENSE) for details.
