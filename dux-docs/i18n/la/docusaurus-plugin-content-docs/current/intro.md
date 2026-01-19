---
id: intro
title: Manuale Constructoris
description: Dux disponere et contribuere
---

# Manuale Constructoris

Haec sectio dispositionem localem, architecturam et normas contributionis tractat.

## Prospectus repositorii

- `server/`: Backend FastAPI et integrationes operum
- `dux-front/`: Frontend Vite + React
- `dux-docs/`: Documentatio in Docusaurus fundata

## Dispositio localis

### Requisita

- Node.js 20+
- Python 3.11+
- Docker (optionale, pro servitiis)

### Gradus

1. Dependentias frontend institue:
    ```bash
    cd dux-front
    npm install
    npm run dev
    ```
2. Backend incipe:
    ```bash
    cd server
    pip install -e .
    uvicorn app:app --reload
    ```
3. Documentationem aedifica:
    ```bash
    cd dux-docs
    npm install
    npm run start
    ```

## Contribuere

- Crea ramos facultatum et PR aperi.
- Scribi probationes pro novis facultatibus.
- Mutationes intentas et documentatas conserva.
