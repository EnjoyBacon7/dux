---
id: intro
title: Guía para desarrolladores
description: Configurar y contribuir a Dux
---

# Guía para desarrolladores

Esta sección cubre la configuración local, la arquitectura y las pautas de contribución.

## Descripción del repositorio

- `server/`: Backend FastAPI e integraciones de empleo
- `dux-front/`: Frontend Vite + React
- `dux-docs/`: Documentación basada en Docusaurus

## Configuración local

### Requisitos

- Node.js 20+
- Python 3.11+
- Docker (opcional, para servicios)

### Pasos

1. Instalar dependencias del frontend:
    ```bash
    cd dux-front
    npm install
    npm run dev
    ```
2. Iniciar el backend:
    ```bash
    cd server
    pip install -e .
    uvicorn app:app --reload
    ```
3. Construir la documentación:
    ```bash
    cd dux-docs
    npm install
    npm run start
    ```

## Contribuir

- Crea ramas de características y abre PR.
- Escribe pruebas para nuevas funciones.
- Mantén los cambios enfocados y documentados.
