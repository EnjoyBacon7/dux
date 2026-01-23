"""
Metiers API router.

Provides endpoints for fetching metier fiche data from the database.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from server.database import get_db_session
from server.models import Metier_ROME, User
from server.dependencies import get_current_user
from server.methods.chat import _call_llm

import logging
from server.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metiers", tags=["Metiers"])


def _map_competences(competences: Any) -> List[Dict[str, str]]:
    if not competences:
        return []

    mapped: List[Dict[str, str]] = []
    for item in competences:
        if isinstance(item, dict):
            label = item.get("libelle") or item.get("label")
            if label:
                mapped.append({"libelle": str(label)})
        elif isinstance(item, str):
            mapped.append({"libelle": item})
    return mapped


@router.get("", summary="List metiers from database")
def list_metiers(
    q: Optional[str] = Query(None, description="Filter by code or libelle"),
    db: Session = Depends(get_db_session),
) -> List[Dict[str, str]]:
    query = db.query(Metier_ROME)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            (Metier_ROME.code.ilike(like)) | (Metier_ROME.libelle.ilike(like))
        )
    rows = query.order_by(Metier_ROME.libelle.asc(), Metier_ROME.code.asc()).all()
    return [{"romeCode": row.code, "romeLibelle": row.libelle or ""} for row in rows]


@router.get("/cv_text", summary="Get current user's cv_text")
async def get_current_user_cv_text(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    cv_text = current_user.cv_text
    if not cv_text:
        return {"cvText": None, "llm": None}
    
    logger.info("OPENAI_BASE_URL=%s", settings.openai_base_url)
    logger.info("OPENAI_API_KEY suffix=%s", settings.openai_api_key)

    prompt = (
        "Here is the text extracted from a CV, I would like to have all the informations "
        "about the jobs the person did or is doing. Please fill this python dictionnary : "
        "{'job_name': [],'job_date':[]}  CV : " + str(cv_text)
    )
    llm_result = await _call_llm(prompt, "")

    return {"cvText": cv_text, "llm": llm_result}


@router.get("/{rome_code}", summary="Get fiche metier from database")
def get_fiche_metier(
    rome_code: str,
    db: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    metier = db.query(Metier_ROME).filter(Metier_ROME.code == rome_code).first()
    if not metier:
        raise HTTPException(status_code=404, detail="Metier not found")

    return {
        "romeCode": metier.code,
        "romeLibelle": metier.libelle
    }
