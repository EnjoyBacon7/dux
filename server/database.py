from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os
from dotenv import load_dotenv  # <--- INDISPENSABLE

# On charge le fichier .env immédiatement
load_dotenv()

# IMPORTANT : L'ordre des imports compte parfois. 
# On importe Base après avoir chargé les variables si besoin, 
# mais ici c'est surtout DATABASE_URL qui compte.
from server.models import Base

# Récupération de l'URL. 
# Si le .env n'est pas lu, ça prend "sqlite://..." et ça plante à cause des ARRAYs.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dux.db")

# Create engine
print(f"🔌 Connexion à la base de données : {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'SQLite (Local)'}")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """
    Initialize the database by creating all tables
    """
    # Création des tables selon les modèles définis dans server/models.py
    Base.metadata.create_all(bind=engine)

@contextmanager
def get_db():
    """
    Context manager for database sessions
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_db_session() -> Session:
    """
    Dependency for FastAPI endpoints to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()