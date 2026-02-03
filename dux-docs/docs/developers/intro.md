---
id: intro
title: Developer Guide
description: Technical documentation, architecture, and complete setup for Dux contributors.
---

# Developer Guide

Welcome to the Dux engineering documentation. This project is a modern full-stack application combining **[FastAPI](https://fastapi.tiangolo.com/)** for intelligent backend processing and **[React](https://react.dev/)** for a responsive frontend experience.

Dux provide a real-time AI analysis via **agentic LLMs and visual models of your choosing** coupled with official job market data(currently just **[France Travail pour les développeurs](https://www.francetravail.io/)**).

---

## Architecture Overview

### Backend (`server/`)
* **Runtime & Manager:** **[Python](https://www.python.org/)** 3.12+ managed by **[uv](https://docs.astral.sh/uv/)**.
* **Framework:** **[FastAPI](https://fastapi.tiangolo.com/)**.
* **Database & ORM:** **[PostgreSQL](https://www.postgresql.org/)** driven by **[SQLAlchemy](https://www.sqlalchemy.org/)**.
* **Configuration:** **[Pydantic](https://docs.pydantic.dev/)** `BaseSettings` for strict environment variable validation.

#### Core Services (`server/services/` & `server/methods/`)
1.  **`MatchingEngine`:**
    * The brain of the application. It constructs context-aware prompts by merging the candidate's CV with job descriptions.
    * Ensure that the LLM returns structured data parsable by the frontend.
2.  **`CVEvaluationPipeline`:**
    * Orchestrates the extraction of data from PDF files.
    * **Step 1 (Text):** Extracts CVs text for the different features.
    * **Step 2 (Structure):** Uses LLM to convert text into a JSON Resume schema.
    * **Step 3 (Visual):** Sends the PDF pages as images to a **VLM (Vision Language Model)** for layout analysis.
3.  **`FT_job_search`:**
    * Handles OAuth2 authentication (Client Credentials flow) with **[France Travail pour les développeurs](https://www.francetravail.io/)**.
    * Manages token rotation and rate limiting automatically.
4.  **`Profile Match`:**
    * Analyzes the candidate's CV to identify the top matching jobs .
    * Proactively fetches offers corresponding to these codes via the France Travail API.
    * Generates a "Justification" string to explain *why* the offer is pushed to the user (e.g., "Matches your skill X").
5.  **`Chatbot Advisor`:**
    * An AI assistant that can help you to get a better profil.
    * Generates a cover letter based on your CV and a given offer.
6.  **`Auth`:**
    * Hybrid authentication system supporting standard Sessions and **Passkeys (WebAuthn)**.

### Frontend (`dux-front/`)
* **Framework:** **[React](https://react.dev/)**  + **[Vite](https://vite.dev/)** + **[TypeScript](https://www.typescriptlang.org/)**.
* **State Management:** React Context API.
* **Styling:** CSS Modules and global CSS variables for theming.
* **Data Fetching:** Custom hooks (`useJobs`, `useCV`) wrapping `fetch`.

---

## Local Setup (Using uv)

The project uses **uv** for ultra-fast Python dependency management. It replaces `pip` and `venv`.

### Prerequisites
* **[Node.js](https://nodejs.org/)** 20+
* **[PostgreSQL](https://www.postgresql.org/)** 15+
* **[uv](https://docs.astral.sh/uv/)** (Install via `pip install uv` or the official installer)
* **[Git](https://git-scm.com/)**

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
    # Using compatible OpenAI Vision endpoint (here we used a key provided by LINAGORA)
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
1.  **Checks** if PostgreSQL is running (and starts it if needed).
2.  **Creates the Database:** Checks for `dux_user` and `dux` DB, creating them if they don't exist.
3.  **Builds Frontend:** Installs npm packages and builds the React app into the static folder.
4.  **Builds Documentation:** Compiles the Docusaurus docs into the static folder.
5.  **Starts Backend:** Launches the FastAPI server with the environment variables.

**Simply run:**
```cmd
./run.bat
```

---


## Local Setup (Using Docker)

If you prefer keeping your environment clean, you can run the entire Dux stack (Database, Backend, and statically served Frontend) using **[Docker](https://www.docker.com/)**.

Our Docker setup uses a **multi-stage build** to compile the React Frontend and Docusaurus documentation, serving everything through a single optimized container.

### Prerequisites
* **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** (Windows/Mac) or **[Docker Engine](https://docs.docker.com/engine/install/)** (Linux).
* **[Git](https://git-scm.com/)**

### 1. Installation & Launch

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/EnjoyBacon7/dux.git
    cd dux
    ```

2.  **Secrets Configuration:**
    Create your `.env` file to provide the necessary API keys.
    ```bash
    cp .env.example .env
    ```
    *Edit `.env` to add your `OPENAI_API_KEY`, `FT_CLIENT_ID`, etc.*
    *> **Note:** You do **not** need to configure `DATABASE_URL` in the .env file for Docker; the `docker-compose.yml` handles the connection to the postgres container automatically.*

3.  **Build and Run:**
    This command builds the frontend, documentation, and backend, then starts the services.
    ```bash
    docker compose up --build -d
    ```

4.  **Access the Application:**
    In Docker mode, the application is served as a production build on a single port:
    * **Full App (Frontend + Backend):** `http://localhost:8080`
    * **API Docs:** `http://localhost:8080/docs`

### Useful Commands

* **Stop containers:** `docker compose down`
* **View logs:** `docker compose logs -f`
* **Rebuild:** `docker compose up --build -d`
* **Clean up:** `docker compose down -v` *(Warning: This deletes the database data)*.