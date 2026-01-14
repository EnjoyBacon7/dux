from fastapi import FastAPI
from database.db import init_db
from routers import jobs, candidats

app = FastAPI(title="DUX - Recrutement IA (Postgres Engine)")

# Initialisation DB au démarrage
@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(jobs.router)
app.include_router(candidats.router)

@app.get("/")
def home():
    return {"message": "API Dux En Ligne 🚀"}