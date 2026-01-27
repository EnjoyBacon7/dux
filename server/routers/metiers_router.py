"""
Metiers API router.

Provides endpoints for fetching metier fiche data from the database.
"""

from typing import Any, Dict, List, Optional, Tuple
import re
from difflib import SequenceMatcher

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from server.database import get_db_session
from server.models import Metier_ROME, User

from server.utils.dependencies import get_current_user
from server.utils.llm import call_llm_async

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
    db: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    rows = (
        db.query(Metier_ROME)
        .order_by(Metier_ROME.libelle.asc(), Metier_ROME.code.asc())
        .all()
    )
    metiers = [{"romeCode": row.code, "romeLibelle": row.libelle or ""} for row in rows]

    cv_text = current_user.cv_text
    if not cv_text:
        return {"cvText": None, "llm": None, "metiers": metiers, "emploisCV": []}

    def _normalize_text(text: str) -> str:
        text = (text or "").lower()
        text = re.sub(r"[^a-zà-ÿ0-9\\s\\-]", " ", text)
        text = re.sub(r"\\s+", " ", text).strip()
        return text

    def _score_match(a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        a_norm = _normalize_text(a)
        b_norm = _normalize_text(b)
        if not a_norm or not b_norm:
            return 0.0
        return SequenceMatcher(None, a_norm, b_norm).ratio()

    def _top_metiers_for_title(title: str, limit: int = 5) -> List[Dict[str, Any]]:
        scored: List[Tuple[float, Metier_ROME]] = []
        for row in rows:
            score = _score_match(title, row.libelle or "")
            if score > 0:
                scored.append((score, row))
        scored.sort(key=lambda item: item[0], reverse=True)
        top = scored[:limit]
        return [
            {"romeCode": row.code, "romeLibelle": row.libelle or "", "score": round(score, 4)}
            for score, row in top
        ]

    max_cv_chars = 6000
    cv_text_llm = cv_text[:max_cv_chars]

    prompt = (
        "Tu es un assistant expert RH. A partir du CV ci-dessous, identifie les emplois "
        "occupes et estime le temps passe dans chaque emploi. Retourne UNIQUEMENT du "
        "JSON valide sans texte additionnel.\n\n"
        "Schema JSON attendu:\n"
        "{\n"
        '  "emplois": [\n'
        "    {\n"
        '      "intitule": "texte du poste dans le CV si disponible",\n'
        '      "dateDebut": "YYYY-MM" | null,\n'
        '      "dateFin": "YYYY-MM" | null,\n'
        '      "dureeMois": number | null\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Contraintes:\n"
        "- Si la duree n'est pas claire, laisse dateDebut/dateFin/dureeMois a null.\n"
        "- Si aucun emploi, retourne une liste vide.\n\n"
        "CV:\n"
        f"{cv_text_llm}\n"
    )

    llm_result = await call_llm_async(
        prompt=prompt,
        system_content="You are a precise JSON-only extractor. Return only valid JSON.",
        temperature=0.2,
        max_tokens=2000,
        parse_json=True,
        json_array=False,
    )
    emplois_cv: List[Dict[str, Any]] = []
    if isinstance(llm_result.get("data"), dict):
        emplois_cv = llm_result["data"].get("emplois") or []

    for emploi in emplois_cv:
        intitule = emploi.get("intitule") or ""
        emploi["topMetiers"] = _top_metiers_for_title(intitule, limit=5)
    print(emplois_cv)
    return {
        "cvText": cv_text,
        "metiers": metiers,
        "emploisCV": emplois_cv,
        "llm": {"model": llm_result.get("model"), "usage": llm_result.get("usage")},
    }

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
