from fastapi import FastAPI
from server.database import init_db
from routers import jobs

# On crée l'application
app = FastAPI(title="DUX - Matching Engine")

# Au démarrage, on crée les tables dans PostgreSQL si elles n'existent pas
@app.on_event("startup")
def on_startup():
    print("🐘 Initialisation de la base de données...")
    init_db()
    print("✅ Tables vérifiées/créées.")

# On inclut notre router de jobs
app.include_router(jobs.router)

@app.get("/")
def home():
    return {"status": "Online", "engine": "PostgreSQL + SQLAlchemy"}