---
id: intro
title: Developer Guide
description: Set up and contribute to Dux
---

# Developer Guide

This section covers local setup, architecture, and contribution guidelines.

## Repository Overview

- `server/`: FastAPI backend and job integrations
- `dux-front/`: Vite + React frontend
- `dux-docs/`: Docusaurus-based documentation

## Local Setup

### Requirements

- Node.js 20+
- Python 3.11+
- Docker (optional, for services)

### Steps

1. Install frontend dependencies:
    ```bash
    cd dux-front
    npm install
    npm run dev
    ```
2. Start backend:
    ```bash
    cd server
    pip install -e .
    uvicorn app:app --reload
    ```
3. Build docs:
    ```bash
    cd dux-docs
    npm install
    npm run start
    ```

## Contributing

- Create feature branches and open PRs.
- Write tests for new features.
- Keep changes focused and documented.
