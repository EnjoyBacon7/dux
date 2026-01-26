"""
Metiers API router.

Provides endpoints for fetching metier fiche data from the database.
"""

from typing import Any, Dict, List, Optional, Tuple
import re
import json
import ast
import difflib

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from server.database import get_db_session
from server.models import Metier_ROME, User
from server.dependencies import get_current_user
from server.methods.chat import _call_llm

import logging

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


def _chunk_list(items: List[Any], size: int) -> List[List[Any]]:
    return [items[i:i + size] for i in range(0, len(items), size)]


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
    db: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    rows = (
        db.query(Metier_ROME)
        .order_by(Metier_ROME.libelle.asc(), Metier_ROME.code.asc())
        .all()
    )
    metiers = [{"romeCode": row.code, "romeLibelle": row.libelle or ""} for row in rows]

    cv_text = current_user.cv_text
    '''if not cv_text:
        return {"cvText": None, "llm": None, "metiers": metiers, "emploisCV": []}'''

    prompt = f"Voici un CV, extrais les emplois occupés avec leur date en conservant le maximum de détails. Retourne uniquement un dictionnaire python au format {{'job_name' : [],'job_time':[],'job_text':[],'job_description':[]}} : {cv_text}"

    llm_emploi = await _call_llm(prompt, "", max_tokens=800)

    prompt = f"A partir de cette liste {json.dumps(llm_emploi)} de poste occupé, rempli un JSON avec ces clés : job_name, job_time, job_text et job_description. En t'assurant de bien mettre l'intitulé du poste dans job_name, la durée convertie en nombre d'année du poste dans job_time (tu peux la chercher dans tous le texte de l'emploi et mettre des virgules), tous le texte de l'emploi dans job_text et enfin dans job_description ajoute un texte que tu auras généré à partir du reste pour décrire le poste occupé. Return ONLY valid JSON, without markdown, without explanation."

    llm_result = await _call_llm(prompt, "", max_tokens=800)

    llm_result = llm_result['data'].replace("```json", "").replace("```", "").strip().replace("\n","")

    llm_result = json.loads(str(llm_result))
    jobs = llm_result
    for job in jobs:
        job.setdefault("romeCode", None)
        job.setdefault("romeLibelle", None)

    for metiers_chunk in _chunk_list(metiers, 200):
        metiers_prompt = (
            "Voici la liste des métiers (ROMECODE + libellé) : "
            f"{json.dumps(metiers_chunk, ensure_ascii=False)}. "
            "Voici la liste des emplois extraits du CV : "
            f"{json.dumps(jobs, ensure_ascii=False)}. "
            "Pour chaque emploi, associe le métier ROME le plus pertinent dans la liste. "
            "Retourne UNIQUEMENT un JSON (liste d'objets) avec les clés : "
            "job_name, job_time, job_text, job_description, romeCode, romeLibelle. "
            "Si aucun métier ne correspond, mets romeCode et romeLibelle à null."
        )

        llm_metiers = await _call_llm(metiers_prompt, "", max_tokens=500)
        llm_metiers = (
            llm_metiers["data"]
            .replace("```json", "")
            .replace("```", "")
            .strip()
            .replace("\n", "")
        )
        chunk_result = json.loads(str(llm_metiers))
        for idx, item in enumerate(chunk_result):
            if idx >= len(jobs):
                break
            if not jobs[idx].get("romeCode") and item.get("romeCode"):
                jobs[idx]["romeCode"] = item.get("romeCode")
                jobs[idx]["romeLibelle"] = item.get("romeLibelle")

    llm_result = jobs

    llm_result = {
        key: [item.get(key) for item in llm_result]
        for key in llm_result[0].keys()
    }

    print(llm_result)

    return llm_result
    


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
