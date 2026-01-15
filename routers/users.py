import os
import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

# --- IMPORTS DE TON PROJET ---
from server.database import get_db_session
from server.models import User

# ✅ On importe les DEUX fonctions de vectorisation
from services.ai_engine import ajouter_cv_vectoriel, ajouter_profil_vectoriel

# ✅ Import de l'outil d'extraction (au singulier 'upload' comme vu ensemble)
try:
    from server.methods.upload import extract_text_from_file
except ImportError:
    # Fallback si le chemin d'import est différent
    from methods.upload import extract_text_from_file

router = APIRouter(prefix="/users", tags=["Utilisateurs"])

# Configuration du dossier d'upload
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)

@router.post("/register")
async def register_user(
    username: str = Form(...),
    email: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    headline: str = Form(None),
    summary: str = Form(None),
    skills: str = Form(None),
    location: str = Form(None),
    cv_file: UploadFile = File(...)
):
    """
    Inscription complète :
    1. Upload du CV (PDF, DOCX, TXT)
    2. Extraction du texte via server.methods.upload
    3. Création User en DB (Postgres)
    4. Vectorisation Hybride (PDF + Profil Déclaratif) dans ChromaDB
    """
    db = next(get_db_session())
    
    # Variables pour le nettoyage en cas d'erreur
    file_path = None 

    try:
        # A. Vérification doublon (Username)
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username déjà pris")

        # B. Sauvegarde du fichier sur le disque
        file_extension = Path(cv_file.filename).suffix.lower()
        
        # Vérification des extensions acceptées
        if file_extension not in [".pdf", ".docx", ".doc", ".txt"]:
            raise HTTPException(status_code=400, detail="Format non supporté. Utilisez PDF, DOCX ou TXT.")

        # Génération d'un nom de fichier sécurisé
        safe_filename = f"{username}_{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / safe_filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(cv_file.file, buffer)

        # C. Extraction du texte (Pour le champ SQL cv_text)
        print(f"📄 Extraction du texte pour {safe_filename}...")
        cv_text_content = extract_text_from_file(file_path, file_extension)
        
        if not cv_text_content or len(cv_text_content) < 10:
            print("⚠️ Attention: Peu ou pas de texte extrait.")

        # D. Traitement des compétences (String -> Liste)
        skills_list = [s.strip() for s in skills.split(",")] if skills else []

        # E. Création de l'utilisateur dans PostgreSQL
        new_user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            headline=headline,
            summary=summary,
            location=location,
            skills=skills_list,
            cv_filename=str(file_path),
            cv_text=cv_text_content 
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # F. Vectorisation IA (Stratégie Double) 🧠
        print(f"🧠 Vectorisation pour l'user {new_user.id}...")
        
        # 1. Le PDF (Preuve factuelle) - Uniquement si c'est un PDF
        if file_extension == ".pdf":
            ajouter_cv_vectoriel(str(file_path), str(new_user.id), f"{first_name} {last_name}")
        else:
            print("ℹ️ Pas de vectorisation fichier (Format non-PDF). Le matching se basera sur le profil.")

        # 2. Le Profil Déclaratif (Intention, Skills, Summary) - TOUJOURS
        ajouter_profil_vectoriel(
            user_id=new_user.id,
            nom=f"{first_name} {last_name}",
            headline=headline,
            summary=summary,
            skills=skills_list
        )

        return {
            "message": "Utilisateur créé avec succès ! (CV + Profil vectorisés)",
            "user_id": new_user.id,
            "username": new_user.username,
            "cv_extracted_length": len(cv_text_content)
        }

    except Exception as e:
        db.rollback()
        # Nettoyage du fichier en cas d'erreur
        if file_path and file_path.exists():
            try:
                file_path.unlink()
            except:
                pass
        print(f"❌ Erreur register: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()