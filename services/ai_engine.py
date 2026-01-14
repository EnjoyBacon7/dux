import os
import difflib
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor # Important pour PostgreSQL
from database.db import get_db_connection

load_dotenv() 

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader

# Configuration
CHROMA_PATH = "chroma_db"
embeddings = OpenAIEmbeddings()

# Initialisation Vector Store
vectorstore = Chroma(
    persist_directory=CHROMA_PATH, 
    embedding_function=embeddings,
    collection_name="candidats_cvs"
)

def get_llm():
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)

def get_vectorstore_retriever(user_id, k=4):
    return vectorstore.as_retriever(
        search_kwargs={"k": k, "filter": {"user_id": user_id}}
    )

def ajouter_cv_vectoriel(file_path, user_id, nom):
    try:
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        for doc in pages:
            doc.metadata["user_id"] = user_id
            doc.metadata["nom"] = nom
        vectorstore.add_documents(pages)
        return True
    except Exception as e:
        print(f"Erreur vectorisation: {e}")
        return False

def supprimer_cv_vectoriel(user_id):
    try:
        vectorstore._collection.delete(where={"user_id": user_id})
        return True
    except Exception:
        return False

def enrichir_requete_avec_ref(titre_offre, description_offre):
    """
    Cherche le métier ROME dans Postgres et ajoute les compétences.
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # 1. Charger les métiers
    cursor.execute("SELECT DISTINCT metier FROM ref_competences")
    metiers_rome = [row["metier"] for row in cursor.fetchall()]
    conn.close()
    
    if not metiers_rome:
        return description_offre

    # 2. Algo de Matching (Mots-clés + Score)
    mots_inutiles = ["le", "la", "les", "de", "du", "des", "et", "ou", "pour", "h/f", "(h/f)"]
    mots_offre = [m for m in titre_offre.lower().replace("/", " ").split() if len(m) > 3 and m not in mots_inutiles]
    
    meilleur_match = None
    meilleur_score = 0

    for metier_db in metiers_rome:
        metier_db_clean = metier_db.lower()
        score = 0
        for mot in mots_offre:
            racine = mot[:-1] if len(mot) > 4 else mot
            if racine in metier_db_clean:
                score += 1
        
        if titre_offre.lower() in metier_db_clean:
            score += 5

        if score > meilleur_score:
            meilleur_score = score
            meilleur_match = metier_db

    # 3. Récupération compétences (Syntaxe Postgres %s)
    if meilleur_match and meilleur_score > 0:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT competence FROM ref_competences 
            WHERE metier = %s AND est_essentiel = TRUE 
            LIMIT 20
        """, (meilleur_match,))
        
        competences = [r["competence"] for r in cursor.fetchall()]
        conn.close()
        
        if competences:
            enrichissement = f"\n\n(CONTEXTE EXPERT ROME - Le métier '{meilleur_match}' implique : {', '.join(competences)})"
            return description_offre + enrichissement
            
    return description_offre