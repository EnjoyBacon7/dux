from fastapi import FastAPI
from server.database import init_db

# 1. On importe le nouveau fichier users
from routers import jobs, users 

app = FastAPI(title="DUX - Matching Engine")

@app.on_event("startup")
def on_startup():
    print("🐘 Initialisation de la base de données...")
    init_db()
    print("✅ Tables vérifiées/créées.")

# 2. On connecte les routes à l'application
app.include_router(jobs.router)
app.include_router(users.router)  # <--- C'est cette ligne qui active /users/register

@app.get("/")
def home():
    return {"status": "Online", "engine": "PostgreSQL + SQLAlchemy"}