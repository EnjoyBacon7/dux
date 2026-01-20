---
id: intro
title: Guia do desenvolvedor
description: Configurar e contribuir para o Dux
---

# Guia do desenvolvedor

Esta seção cobre a configuração local, arquitetura e diretrizes de contribuição.

## Visão geral do repositório

- `server/`: Backend FastAPI e integrações de emprego
- `dux-front/`: Frontend Vite + React
- `dux-docs/`: Documentação baseada em Docusaurus

## Configuração local

### Requisitos

- Node.js 20+
- Python 3.11+
- Docker (opcional, para serviços)

### Passos

1. Instalar dependências do frontend:
    ```bash
    cd dux-front
    npm install
    npm run dev
    ```
2. Iniciar o backend:
    ```bash
    cd server
    pip install -e .
    uvicorn app:app --reload
    ```
3. Construir a documentação:
    ```bash
    cd dux-docs
    npm install
    npm run start
    ```

## Contribuir

- Crie branches de recursos e abra PRs.
- Escreva testes para novos recursos.
- Mantenha as mudanças focadas e documentadas.
