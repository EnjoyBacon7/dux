"""Profile management router.

Provides endpoints for user profile setup, CV upload, and experience/education management.
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import mimetypes

from server.methods.upload import UPLOAD_DIR, upload_file
from server.database import get_db_session
from server.models import User, Metier_ROME
from server.utils.dependencies import get_current_user

# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(prefix="/profile", tags=["Profile"])
logger = logging.getLogger(__name__)

# ============================================================================
# Request Models
# ============================================================================

# ============================================================================
# File Upload Endpoints
# ============================================================================


@router.post("/upload", summary="Upload CV file")
async def upload_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Upload and process a CV file (PDF, DOCX, or TXT).

    Handles file validation, text extraction, and storage of CV data
    in the user's profile. Automatically triggers CV evaluation in the background.

    Args:
        request: FastAPI request object
        background_tasks: FastAPI background tasks
        file: The CV file to upload (multipart/form-data)
        db: Database session
        current_user: Current authenticated user

    Returns:
        dict: Upload result with filename, content_type, size, extracted_text, and status message

    Raises:
        HTTPException: If file validation or processing fails
    """
    result = await upload_file(file)

    # Update user's CV filename and extracted text in database
    current_user.cv_filename = result["filename"]
    current_user.cv_text = result["extracted_text"]

    model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2",local_files_only=True)
    
    # Extracting the experience section from the current user cv
    cv_text = current_user.cv_text

    prompt = f"Voici le texte d'un CV : \n{cv_text}\n Renvoie moi le texte des expériences professionnelles avec le maximum de texte, ajoute une description complète de l'experience. REND MOI LA LISTE DES EXPERIENCES PROFESSIONNELLES SEPARE PAR [EMPLOI]. SURTOUT N'AJOUTE PAS DE TEXTE AUTOUR DE LA REPONSE."
    liste_xp = await _call_llm(prompt,"")
    liste_xp = liste_xp['data'].split("[EMPLOI]")
    
    # Extraction of experience
    rows = (
        db.query(Metier_ROME)
        .order_by(Metier_ROME.libelle.asc(), Metier_ROME.code.asc())
        .all()
    )
    metiers = [(row.libelle or "", row.code, row.libelle_embedded) for row in rows]

    emploi_occupe = {"Job_name" : [], "Job_description" : []}
    for experience in liste_xp:
        score = []
        print(experience)
        if not experience or not experience.strip():
            continue

        prompt = f"Donne moi le nom du métier de cette description : {experience}. Ne renvoie que le nom du métier, rien d'autre."
        experience_simplifiee = await _call_llm(prompt,"")
        experience_embedded = model.encode([str(experience_simplifiee['data'])], normalize_embeddings=True)
        for metier_label, metier_code, metier_embedded in metiers:
            if not metier_label:
                continue

            score.append(((metier_label, metier_code), cosine_similarity(experience_embedded, metier_embedded)[0][0]))

        if not score:
            logger.warning("No metiers to score for experience: %s", experience)
            continue

        score.sort(key=lambda item: item[1], reverse=True)

        prompt = f"A quel métier de cette liste : {score[0:2]} cette description correspond le plus : {experience}. Ne renvoie que l'indice du métier correspondant le plus (soit 0, soit 1, soit 2), rien d'autre."
        data = await _call_llm(prompt,"")
        indice_meilleur_metier = data['data']

        print(indice_meilleur_metier)
        print(score[0:3])

        emploi_occupe['Job_name'].append(score[int(indice_meilleur_metier)][0])
        emploi_occupe['Job_description'].append(experience)

    print(emploi_occupe)

    duree = []

    for (job_label, rome_code), desc in zip(emploi_occupe["Job_name"], emploi_occupe["Job_description"]):
        prompt = f"Voici la description d'un emploi extraite d'un CV. Rend moi la partie qui parle des dates de prise de poste en la traduisant en français. Rend moi uniquement le morceau du texte en français avec rien autour : {desc}"
        data = await _call_llm(prompt,"")
        duree_text = data['data']
        print(duree_text)

        duree.append(extract_periods_fr(duree_text))

    emploi_occupe['duree'] = duree




    db.commit()

    # Trigger CV evaluation in the background
    if result.get("extracted_text"):
        from server.routers.cv_router import run_cv_evaluation
        from server.database import SessionLocal
        from server.scheduler import generate_optimal_offers_for_user

        background_tasks.add_task(
            run_cv_evaluation,
            user_id=current_user.id,
            cv_text=result["extracted_text"],
            cv_filename=result["filename"],
            db_session_factory=SessionLocal,
        )
        result["evaluation_status"] = "started"
        logger.info(f"CV evaluation triggered for user {current_user.id}")

        # Trigger optimal offers generation after CV upload
        # Create a new database session for the background task
        def generate_offers_task():
            """Background task to generate optimal offers after CV upload."""
            import asyncio
            db_session = SessionLocal()
            try:
                asyncio.run(generate_optimal_offers_for_user(current_user.id, db_session))
                logger.info(f"Optimal offers generation triggered for user {current_user.id}")
            except Exception as e:
                logger.error(f"Error generating optimal offers for user {current_user.id}: {str(e)}")
            finally:
                db_session.close()

        background_tasks.add_task(generate_offers_task)
        result["optimal_offers_status"] = "started"

    return result


@router.get("/cv", summary="Get current user's CV file")
async def get_cv_file(
    current_user: User = Depends(get_current_user)
):
    """
    Return the authenticated user's CV file for inline display/download.

    Ensures the user has a CV on record and that the file exists on disk
    before streaming it back to the client.
    """
    if not current_user.cv_filename:
        raise HTTPException(status_code=404, detail="No CV found for this user")

    upload_root = UPLOAD_DIR.resolve()
    file_path = (UPLOAD_DIR / current_user.cv_filename).resolve()

    # Prevent path traversal outside the upload directory
    if upload_root not in file_path.parents:
        raise HTTPException(status_code=400, detail="Invalid CV path")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="CV file not found")

    media_type, _ = mimetypes.guess_type(current_user.cv_filename)
    headers = {"Content-Disposition": f'inline; filename="{current_user.cv_filename}"'}

    return FileResponse(
        path=file_path,
        media_type=media_type or "application/octet-stream",
        headers=headers
    )
