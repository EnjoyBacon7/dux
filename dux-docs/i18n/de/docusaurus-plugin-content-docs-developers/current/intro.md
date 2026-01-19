---
id: intro
title: Entwicklerhandbuch
description: Dux einrichten und dazu beitragen
---

# Entwicklerhandbuch

Dieser Abschnitt behandelt die lokale Einrichtung, Architektur und Beitragsrichtlinien.

## Repository-Übersicht

- `server/`: FastAPI-Backend und Job-Integrationen
- `dux-front/`: Vite + React Frontend
- `dux-docs/`: Docusaurus-basierte Dokumentation

## Lokale Einrichtung

### Voraussetzungen

- Node.js 20+
- Python 3.11+
- Docker (optional, für Dienste)

### Schritte

1. Frontend-Abhängigkeiten installieren:
    ```bash
    cd dux-front
    npm install
    npm run dev
    ```
2. Backend starten:
    ```bash
    cd server
    pip install -e .
    uvicorn app:app --reload
    ```
3. Dokumentation erstellen:
    ```bash
    cd dux-docs
    npm install
    npm run start
    ```

## Beitragen

- Erstellen Sie Feature-Branches und öffnen Sie PRs.
- Schreiben Sie Tests für neue Funktionen.
- Halten Sie Änderungen fokussiert und dokumentiert.
