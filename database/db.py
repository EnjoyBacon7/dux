import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Crée une connexion PostgreSQL."""
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        return conn
    except Exception as e:
        print(f"❌ Erreur de connexion DB : {e}")
        return None

def init_db():
    """Crée les tables PostgreSQL si nécessaire."""
    conn = get_db_connection()
    if not conn:
        print("⚠️ Pas de connexion DB, impossible d'initialiser les tables.")
        return
    
    cur = conn.cursor()
    print("🐘 Initialisation des tables PostgreSQL...")

    # Table UTILISATEURS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            nom VARCHAR(100),
            role VARCHAR(50) DEFAULT 'candidat',
            infos_json JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Table JOBS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id SERIAL PRIMARY KEY,
            titre VARCHAR(255) NOT NULL,
            description TEXT,
            ville VARCHAR(100),
            type_contrat VARCHAR(50),
            salaire VARCHAR(100),
            details_sup JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Table CANDIDATS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS candidats (
            id VARCHAR(50) PRIMARY KEY,
            nom VARCHAR(255),
            infos TEXT,
            chemin_cv VARCHAR(500),
            user_id INTEGER REFERENCES users(id)
        );
    """)

    # Table ROME
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ref_competences (
            id SERIAL PRIMARY KEY,
            metier VARCHAR(255),
            categorie VARCHAR(255),
            competence VARCHAR(255),
            est_essentiel BOOLEAN
        );
    """)
    
    # Index
    cur.execute("CREATE INDEX IF NOT EXISTS idx_rome_metier ON ref_competences(metier);")

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Tables prêtes.")

if __name__ == "__main__":
    init_db()