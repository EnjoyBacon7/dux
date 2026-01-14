import os
import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from database.db import get_db_connection
from services.ai_engine import ajouter_cv_vectoriel, supprimer_cv_vectoriel
from psycopg2.extras import RealDictCursor

router = APIRouter(prefix="/candidats", tags=["Candidats"])
UPLOAD_DIR = "cvs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/")
async def ajouter_candidat(
    nom: str = Form(...), 
    infos: str = Form(...), 
    fichier: UploadFile = File(...)
):
    user_id = str(uuid.uuid4())
    file_location = f"{UPLOAD_DIR}/{user_id}_{fichier.filename}"
    
    # 1. Sauvegarde Fichier
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(fichier.file, file_object)
    
    # 2. Sauvegarde SQL (Postgres)
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO candidats (id, nom, infos, chemin_cv) 
            VALUES (%s, %s, %s, %s)
        """, (user_id, nom, infos, file_location))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        return {"error": f"Erreur SQL: {str(e)}"}

    # 3. Vectorisation
    ajouter_cv_vectoriel(file_location, user_id, nom)

    return {"status": "success", "user_id": user_id}

@router.delete("/{user_id}")
async def supprimer_candidat(user_id: str):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT chemin_cv FROM candidats WHERE id = %s", (user_id,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        raise HTTPException(status_code=404, detail="Inconnu")
    
    # Nettoyage
    cursor.execute("DELETE FROM candidats WHERE id = %s", (user_id,))
    conn.commit()
    conn.close()

    if os.path.exists(result["chemin_cv"]):
        os.remove(result["chemin_cv"])
    
    supprimer_cv_vectoriel(user_id)

    return {"message": "Suppression effectuée"}