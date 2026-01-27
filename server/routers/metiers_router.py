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

from server.utils.dependencies import get_current_user
from server.utils.llm import call_llm_async

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

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

    import re
import unicodedata
from typing import List, Dict, Optional


def extract_periods_fr(text: str) -> List[Dict[str, Optional[int]]]:
    """
    Extrait des périodes (start/end) depuis un texte FR (CV).
    Retourne une liste de dicts:
      - start_year, start_month (optionnel)
      - end_year, end_month (optionnel)
      - ongoing (bool)
      - raw (extrait texte correspondant)
    """

    def normalize_fr(s: str) -> str:
        s = s.upper()
        s = unicodedata.normalize("NFD", s)
        s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")  # enlève accents
        # Harmonise quelques apostrophes/traits
        s = s.replace("’", "'").replace("–", "-").replace("—", "-")
        return s

    MOIS_MAP = {
        "JANVIER": 1, "JANV": 1, "JAN": 1,
        "FEVRIER": 2, "FEVR": 2, "FEV": 2,
        "MARS": 3,
        "AVRIL": 4, "AVR": 4,
        "MAI": 5,
        "JUIN": 6,
        "JUILLET": 7, "JUIL": 7,
        "AOUT": 8, "AOU": 8,
        "SEPTEMBRE": 9, "SEPT": 9, "SEP": 9,
        "OCTOBRE": 10, "OCT": 10,
        "NOVEMBRE": 11, "NOV": 11,
        "DECEMBRE": 12, "DEC": 12,
    }

    MONTH_TOKEN = r"(JANVIER|JANV|JAN|FEVRIER|FEVR|FEV|MARS|AVRIL|AVR|MAI|JUIN|JUILLET|JUIL|AOUT|AOU|SEPTEMBRE|SEPT|SEP|OCTOBRE|OCT|NOVEMBRE|NOV|DECEMBRE|DEC)"
    YEAR_TOKEN = r"(19\d{2}|20\d{2})"

    # Termes "en cours"
    ONGOING_TOKEN = r"(PRESENT|AUJOURD'HUI|AUJOURD HUI|EN COURS|ACTUELLEMENT|A CE JOUR|JUSQUA PRESENT|CURRENT|NOW)"

    # Start: soit MOIS+ANNEE soit ANNEE seule
    START = rf"(?:(?P<sm>{MONTH_TOKEN})\.?\s*(?P<sy>{YEAR_TOKEN})|(?P<sy_only>{YEAR_TOKEN}))"
    # End: MOIS+ANNEE, ANNEE seule, ou ongoing
    END = rf"(?:(?P<em>{MONTH_TOKEN})\.?\s*(?P<ey>{YEAR_TOKEN})|(?P<ey_only>{YEAR_TOKEN})|(?P<ongoing>{ONGOING_TOKEN}))"

    # Séparateurs d'intervalle
    SEP = r"\s*(?:-|\bA\b|\bAU\b|\bAUX\b|\bJUSQU'?A\b|\bTO\b)\s*"

    # Intervalle générique, optionnellement précédé de "DE"
    RE_RANGE = re.compile(rf"(?:\bDE\s+)?{START}{SEP}{END}")
    # "DEPUIS <date>" => ongoing
    RE_DEPUIS = re.compile(rf"\bDEPUIS\s+{START}")

    t = normalize_fr(text)
    periods: List[Dict[str, Optional[int]]] = []

    def _build_period(m, ongoing_forced: bool = False, raw_override: Optional[str] = None):
        sm = m.group("sm")
        sy = m.group("sy") or m.group("sy_only")
        em = m.group("em")
        ey = m.group("ey") or m.group("ey_only")
        ongoing_hit = m.group("ongoing")

        start_year = int(sy) if sy else None
        start_month = MOIS_MAP[sm] if sm else None

        if ongoing_forced or ongoing_hit:
            end_year = None
            end_month = None
            ongoing = True
        else:
            end_year = int(ey) if ey else None
            end_month = MOIS_MAP[em] if em else None
            ongoing = False

        periods.append({
            "start_year": start_year,
            "start_month": start_month,
            "end_year": end_year,
            "end_month": end_month,
            "ongoing": ongoing,
            "raw": raw_override if raw_override is not None else m.group(0).strip()
        })

    # 1) Récupère d'abord les "DEPUIS ..." (emploi en cours)
    for m in RE_DEPUIS.finditer(t):
        _build_period(m, ongoing_forced=True, raw_override=m.group(0).strip())

    # 2) Puis les intervalles classiques
    for m in RE_RANGE.finditer(t):
        _build_period(m)

    # 3) Dé-doublonnage simple (mêmes start/end/ongoing)
    seen = set()
    unique = []
    for p in periods:
        key = (p["start_year"], p["start_month"], p["end_year"], p["end_month"], p["ongoing"])
        if key not in seen:
            seen.add(key)
            unique.append(p)

    return unique



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
    
    model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2",local_files_only=True)
    
    # Extracting the experience section from the current user cv
    cv_text = current_user.cv_text

    prompt = f"Voici le texte d'un CV : \n{cv_text}\n Renvoie moi le texte des expériences professionnelles avec le maximum de texte, ajoute une description complète de l'experience. REND MOI LA LISTE DES EXPERIENCES PROFESSIONNELLES SEPARE PAR [EMPLOI]. SURTOUT N'AJOUTE PAS DE TEXTE AUTOUR DE LA REPONSE."
    liste_xp = await call_llm_async(prompt,"")
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
        experience_simplifiee = await call_llm_async(prompt,"")
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
        data = await call_llm_async(prompt,"")
        indice_meilleur_metier = data['data']

        print(indice_meilleur_metier)
        print(score[0:3])

        emploi_occupe['Job_name'].append(score[int(indice_meilleur_metier)][0])
        emploi_occupe['Job_description'].append(experience)

    print(emploi_occupe)

    duree = []

    for (job_label, rome_code), desc in zip(emploi_occupe["Job_name"], emploi_occupe["Job_description"]):
        prompt = f"Voici la description d'un emploi extraite d'un CV. Rend moi la partie qui parle des dates de prise de poste en la traduisant en français. Rend moi uniquement le morceau du texte en français avec rien autour : {desc}"
        data = await call_llm_async(prompt,"")
        duree_text = data['data']
        print(duree_text)

        duree.append(extract_periods_fr(duree_text))

    emploi_occupe['duree'] = duree

    print(emploi_occupe)

    return emploi_occupe
    
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
