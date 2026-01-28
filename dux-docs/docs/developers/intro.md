---
id: intro
title: Developer Guide
description: Technical documentation, architecture, and setup for Dux
---

# Developer Guide 👨‍💻

Welcome to the Dux engineering documentation. This project is a modern full-stack application combining **FastAPI** (Python) and **React** (Vite), orchestrated to provide real-time AI analysis via **OpenAI** and job market data via **France Travail**.

## Architecture Overview

### Backend (`/server`)
* **Runtime & Manager:** Python 3.12+ managed by **uv**.
* **Framework:** FastAPI (Async).
* **ORM:** SQLAlchemy (PostgreSQL for prod).
* **Configuration:** Pydantic `BaseSettings` (Strict environment variable validation).
* **Core Services:**
    * `MatchingEngine`: OpenAI wrapper for CV analysis and strict JSON parsing.
    * `FT_job_search`: Interface for OAuth2 and France Travail Search API.
    * `Auth`: Hybrid authentication (Session-based + Passkeys/WebAuthn + LinkedIn OAuth).

### Frontend (`/dux-front`)
* **Framework:** React 18 + Vite + TypeScript.
* **State Management:** React Context API (`AuthContext`, `LanguageContext`).
* **Styling:** CSS Modules and global CSS variables.
* **I18n:** Custom translation system via the `useLanguage` hook.

---

## Local Setup (Using uv)

The project uses **uv** for ultra-fast Python dependency management.

### Prerequisites
* **Node.js** 20+
* **uv** (Install via `pip install uv` or the official installer)
* **Git**

### 1. Backend Installation

1.  Clone the repository and navigate to the root (where `uv.lock` is located):
    ```bash
    git clone https://github.com/EnjoyBacon7/dux.git
    cd dux
    ```

2.  **Install Dependencies:**
    This command automatically creates the virtual environment (`.venv`) and syncs all dependencies instantly.
    ```bash
    uv sync
    ```

3.  **Secrets Configuration (CRITICAL):**
    Duplicate the `.env.example` file to `.env` in the root directory.
    ```bash
    cp .env.example .env
    ```
    
    You **must** define the following variables in `.env` for the application to start (otherwise Pydantic will block the startup):

    ```ini
    # --- APP ---
    SECRET_KEY=your_secure_secret_key
    
    # --- AI (Required for Matching) ---
    OPENAI_API_KEY=sk-xxxx...
    OPENAI_MODEL=gpt-4o-mini  # or another compatible model

    # --- FRANCE TRAVAIL (Required for Job Search) ---
    # Get these keys at: https://www.emploi-store-dev.fr/portail-developpeur
    FT_CLIENT_ID=your_client_id
    FT_CLIENT_SECRET=your_client_secret
    
    # API URLs (Do not modify unless the API endpoints change)
    FT_AUTH_URL=https://entreprise.francetravail.fr/connexion/oauth2/access_token
    FT_API_URL_OFFRES=https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search
    FT_API_URL_FICHE_METIER=https://api.francetravail.io/partenaire/rome-metiers/v1/metiers/metier?champs=accesemploi,code,centresInteretsLies
    ```

4.  **Start the Server:**
    Use `uv run` to execute the server within the virtual environment context.
    ```bash
    # Option A: Windows Script (Recommended)
    ./run.bat

    # Option B: Manual Command (Linux/Mac/Windows)
    uv run uvicorn server.app:app --reload --port 8000
    ```

### 2. Frontend Installation

Open a new terminal window:

1.  Navigate to the frontend directory:
    ```bash
    cd dux-front
    ```
2.  Install and Run:
    ```bash
    npm install
    npm run dev
    ```
3.  The application is accessible at `http://localhost:5173`.

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

**Note on AI:** The backend automatically detects the user's language and injects a "System Prompt" instructing the LLM to reply in that language, while maintaining the technical JSON structure required by the frontend.

---

## Key Concepts

### ROME Codes
France Travail uses ROME codes (e.g., *M1805 - IT Studies and Development*) to categorize jobs.
* **Backend:** We map user keywords to these codes to broaden search results.
* **Matching:** The AI compares the standard skills associated with the ROME code against the CV, rather than just matching job titles.

### Contribution Guidelines
* **Never commit the `.env` file.**
* If you add a new environment variable, update the Pydantic model in `server/config.py`.
* Run `uv sync` if you modify Python dependencies.