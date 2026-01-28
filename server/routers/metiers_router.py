"""
Metiers API router.

Provides endpoints for fetching metier fiche data from the database
and for user favourite occupations (Tracker feature).
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from server.database import get_db_session
from server.models import FavouriteMetier, Metier_ROME, User
from server.utils.dependencies import get_current_user

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metiers", tags=["Metiers"])


class AddFavouritePayload(BaseModel):
    romeCode: str
    romeLibelle: Optional[str] = None


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


# ---------------------------------------------------------------------------
# Favourites (Tracker) – must be defined before /{rome_code}
# ---------------------------------------------------------------------------


@router.get("/favourites", summary="List current user's favourite occupations")
def list_favourites(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    rows = (
        db.query(FavouriteMetier)
        .filter(FavouriteMetier.user_id == current_user.id)
        .order_by(FavouriteMetier.created_at.desc())
        .all()
    )
    return [
        {
            "romeCode": r.rome_code,
            "romeLibelle": r.rome_libelle or r.rome_code,
            "addedAt": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.post("/favourites", summary="Add occupation to favourites")
def add_favourite(
    payload: AddFavouritePayload,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    code = (payload.romeCode or "").strip()
    if not code:
        raise HTTPException(status_code=400, detail="romeCode is required")
    existing = (
        db.query(FavouriteMetier)
        .filter(
            FavouriteMetier.user_id == current_user.id,
            FavouriteMetier.rome_code == code,
        )
        .first()
    )
    if existing:
        return {
            "romeCode": existing.rome_code,
            "romeLibelle": existing.rome_libelle or existing.rome_code,
            "addedAt": existing.created_at.isoformat() if existing.created_at else None,
        }
    libelle = (payload.romeLibelle or "").strip() or None
    fm = FavouriteMetier(
        user_id=current_user.id,
        rome_code=code,
        rome_libelle=libelle,
    )
    db.add(fm)
    db.commit()
    db.refresh(fm)
    return {
        "romeCode": fm.rome_code,
        "romeLibelle": fm.rome_libelle or fm.rome_code,
        "addedAt": fm.created_at.isoformat() if fm.created_at else None,
    }


@router.delete("/favourites/{rome_code}", summary="Remove occupation from favourites")
def remove_favourite(
    rome_code: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> None:
    row = (
        db.query(FavouriteMetier)
        .filter(
            FavouriteMetier.user_id == current_user.id,
            FavouriteMetier.rome_code == rome_code,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Favourite not found")
    db.delete(row)
    db.commit()
    return None


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
