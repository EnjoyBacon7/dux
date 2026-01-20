---
id: intro
title: Guide du développeur
description: Configurer et contribuer à Dux
---

# Guide du développeur

Cette section couvre la configuration locale, l'architecture et les directives de contribution.

## Aperçu du dépôt

- `server/`: Backend FastAPI et intégrations d'emploi
- `dux-front/`: Frontend Vite + React
- `dux-docs/`: Documentation basée sur Docusaurus

## Configuration locale

### Prérequis

- Node.js 20+
- Python 3.11+
- Docker (optionnel, pour les services)

### Étapes

1. Installer les dépendances du frontend :
    ```bash
    cd dux-front
    npm install
    npm run dev
    ```
2. Démarrer le backend :
    ```bash
    cd server
    pip install -e .
    uvicorn app:app --reload
    ```
3. Construire la documentation :
    ```bash
    cd dux-docs
    npm install
    npm run start
    ```

## Contribuer

- Créez des branches de fonctionnalités et ouvrez des PR.
- Écrivez des tests pour les nouvelles fonctionnalités.
- Gardez les modifications ciblées et documentées.
