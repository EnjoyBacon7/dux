---
id: intro
title: Developer Guide
description: Technical documentation, architecture, and complete setup for Dux contributors.
---

# Developer Guide 👨‍💻

Welcome to the Dux engineering documentation. This project is a modern full-stack application combining **FastAPI** (Python) for intelligent backend processing and **React** (Vite) for a responsive frontend experience.

Dux is architected to provide real-time AI analysis via **OpenAI** (LLM) & **Lucie/Linagora** (VLM), coupled with official job market data from **France Travail**.

---

## Architecture Overview

### Backend (`/server`)
* **Runtime & Manager:** Python 3.12+ managed by **uv** (An extremely fast Python package installer and resolver).
* **Framework:** FastAPI (Async/Await based).
* **Database & ORM:** PostgreSQL driven by **SQLAlchemy** (async session management).
* **Migrations:** **Alembic** handles schema changes.
* **Configuration:** Pydantic `BaseSettings` for strict environment variable validation.

#### Core Services (`/server/services` & `/server/methods`)
1.  **`MatchingEngine`:**
    * The brain of the application. It constructs context-aware prompts by merging the candidate's raw text (`cv_text`) with job descriptions.
    * Uses "Strict JSON Mode" to ensure the LLM returns structured data parsable by the frontend.
2.  **`CVEvaluationPipeline`:**
    * Orchestrates the extraction of data from PDF files.
    * **Step 1 (Text):** Extracts raw text for the "Fast Match" feature.
    * **Step 2 (Structure):** Uses LLM to convert text into a JSON Resume schema.
    * **Step 3 (Visual):** Sends the PDF pages as images to a **VLM (Vision Language Model)** for layout analysis.
3.  **`FT_job_search`:**
    * Handles OAuth2 authentication (Client Credentials flow) with France Travail.
    * Manages token rotation and rate limiting automatically.
4.  **`Profile Match`:**
    * Analyzes the candidate's CV to identify the top matching jobs .
    * Proactively fetches offers corresponding to these codes via the France Travail API.
    * Generates a "Justification" string to explain *why* the offer is pushed to the user (e.g., "Matches your skill X").
5.  **`Auth`:**
    * Hybrid authentication system supporting standard Sessions and **Passkeys (WebAuthn)**.

### Frontend (`/dux-front`)
* **Framework:** React 18 + Vite + TypeScript.
* **State Management:** React Context API (`AuthContext` for user session, `LanguageContext` for i18n).
* **Styling:** CSS Modules and global CSS variables for theming.
* **Data Fetching:** Custom hooks (`useJobs`, `useCV`) wrapping `fetch`.

---

## Local Setup (Using uv)

The project uses **uv** for ultra-fast Python dependency management. It replaces `pip` and `venv`.

### Prerequisites
* **Node.js** 20+
* **PostgreSQL** 15+ (Running locally or via Docker)
* **uv** (Install via `pip install uv` or the official installer)
* **Git**

### 1. Backend Installation

1.  Clone the repository and navigate to the root:
    ```bash
    git clone https://github.com/EnjoyBacon7/dux.git
    cd dux
    ```

2.  **Install Dependencies:**
    This command automatically creates the virtual environment (`.venv`) and syncs all dependencies defined in `pyproject.toml`.
    ```bash
    uv sync
    ```

3.  **Secrets Configuration (CRITICAL):**
    Duplicate the `.env.example` file to `.env` in the root directory.
    ```bash
    cp .env.example .env
    ```
    
    **Fill in your `.env` file carefully.** The application will fail to start if required keys are missing.

    ```ini
    # --- DATABASE ---
    # Ensure this DB exists in your local Postgres
    DATABASE_URL=postgresql://dux_user:dux_password@localhost:5432/dux

    # --- APP CONFIG ---
    UPLOAD_DIR=./uploads
    EVALUATION_DIR=./evaluations
    HOST=0.0.0.0
    PORT=8000

    # --- SECURITY ---
    # Generate a secure key: python -c "import secrets; print(secrets.token_hex(32))"
    SESSION_SECRET=change_this_to_a_random_string
    SESSION_COOKIE_NAME=dux_session
    SESSION_MAX_AGE=86400
    SESSION_COOKIE_SECURE=false # Set to true in Production (HTTPS)
    SESSION_COOKIE_HTTPONLY=true
    SESSION_COOKIE_SAMESITE=lax

    # --- CORS & ORIGINS ---
    # Important for frontend communication
    CORS_ORIGINS=http://localhost:5173,http://localhost:8080
    CORS_ALLOW_CREDENTIALS=true
    
    # --- WEBAUTHN / PASSKEYS ---
    RP_ID=localhost
    RP_NAME=Dux
    ORIGIN=http://localhost:5173

    # --- AI SERVICES ---
    # LLM (Text Analysis & Matching)
    OPENAI_API_KEY=sk-your-openai-key
    OPENAI_MODEL=gpt-4o-mini
    
    # VLM (Visual CV Analysis)
    # Using compatible OpenAI Vision endpoint (here we used Lucie/Linagora)
    VLM_API_KEY=sk-your-vlm-key
    VLM_MODEL=lucie-7b-instruct
    VLM_BASE_URL=https://chat.lucie.ovh.linagora.com/v1

    # --- FRANCE TRAVAIL API ---
    # Register at: https://www.emploi-store-dev.fr/portail-developpeur
    FT_CLIENT_ID=your_ft_client_id
    FT_CLIENT_SECRET=your_ft_client_secret
    
    # FT Endpoints 
    FT_AUTH_URL=https://entreprise.francetravail.fr/connexion/oauth2/access_token
    FT_API_URL_OFFRES=https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search
    FT_API_URL_FICHE_METIER=https://api.francetravail.io/partenaire/rome-metiers/v1/metiers/metier
    FT_API_URL_CODE_METIER=https://api.francetravail.io/partenaire/rome-metiers/v1/metiers/metier?champs=code,libelle
    FT_API_URL_FICHE_COMPETENCE=https://api.francetravail.io/partenaire/rome-competences/v1/competences/competence
    FT_API_URL_CODE_COMPETENCE=https://api.francetravail.io/partenaire/rome-competences/v1/competences/competence?champs=code,libelle
    ```

#### Automated Setup

We provide a robust `run.bat` script that handles the entire stack.
**It automatically:**
1.  Checks if PostgreSQL is running (and starts it if needed).
2.  **Creates the Database:** Checks for `dux_user` and `dux` DB, creating them if they don't exist.
3.  **Builds Frontend:** Installs npm packages and builds the React app into the static folder.
4.  **Builds Documentation:** Compiles the Docusaurus docs into the static folder.
5.  **Starts Backend:** Launches the FastAPI server with the environment variables.

**Simply run:**
```cmd
./run.bat
```
---

## Internationalization (i18n) Guide

The project supports dynamic language switching (`en`, `fr`, `es`, `pt`, `de`, `la`).

**To add a new translation:**
1.  Open `dux-front/src/contexts/LanguageContext.tsx`.
2.  Add your key to the `translations` object:
    ```typescript
    'my.new.text': {
        en: 'My new text',
        fr: 'Mon nouveau texte',
        es: 'Mi nuevo texto'
    }
    ```
3.  Use the hook in your React component:
    ```tsx
    const { t } = useLanguage();
    <p>{t('my.new.text')}</p>
    ```

**Note on AI:** The backend automatically detects the user's language preference and injects a "System Prompt" instructing the LLM to reply in that language, while maintaining the technical JSON structure required by the frontend.

---

## Contribution Guidelines

* **Never commit the `.env` file.**
* If you modify the DB Models (`server/models.py`), you MUST modify your database too.
* Run `uv sync` if you modify Python dependencies.