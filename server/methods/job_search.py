"""
Job search and filtering utilities.

Provides database queries for searching job offers with full-text search,
filtering, and pagination capabilities.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ============================================================================
# Search Configuration
# ============================================================================

# Full list of columns to return for each job offer
JOB_COLUMNS: List[str] = [
    "id",
    "intitule",
    "description",
    "dateCreation",
    "dateActualisation",
    "romeCode",
    "romeLibelle",
    "appellationlibelle",
    "typeContrat",
    "typeContratLibelle",
    "natureContrat",
    "experienceExige",
    "experienceLibelle",
    "competences",
    "dureeTravailLibelle",
    "dureeTravailLibelleConverti",
    "alternance",
    "nombrePostes",
    "accessibleTH",
    "qualificationCode",
    "qualificationLibelle",
    "codeNAF",
    "secteurActivite",
    "secteurActiviteLibelle",
    "offresManqueCandidats",
    "entrepriseAdaptee",
    "employeurHandiEngage",
    "lieuTravail_libelle",
    "lieuTravail_latitude",
    "lieuTravail_longitude",
    "lieuTravail_codePostal",
    "lieuTravail_commune",
    "entreprise_nom",
    "entreprise_entrepriseAdaptee",
    "salaire_libelle",
    "contact_nom",
    "contact_coordonnees1",
    "contact_courriel",
    "origineOffre_origine",
    "origineOffre_urlOrigine",
    "contexteTravail_horaires",
    "formations",
    "qualitesProfessionnelles",
    "salaire_complement1",
    "salaire_listeComplements",
    "trancheEffectifEtab",
    "experienceCommentaire",
    "permis",
    "salaire_complement2",
    "contact_coordonnees2",
    "contact_coordonnees3",
    "agence_courriel",
    "salaire_commentaire",
    "deplacementCode",
    "deplacementLibelle",
    "entreprise_logo",
    "contact_urlPostulation",
    "contexteTravail_conditionsExercice",
    "langues",
    "entreprise_description",
    "contact_telephone",
    "entreprise_url",
]

# Subset of columns used for basic full-text search
SEARCHABLE_COLUMNS: List[str] = [
    "intitule",
    "description",
    "romeLibelle",
    "appellationlibelle",
    "lieuTravail_libelle",
    "entreprise_nom",
    "secteurActiviteLibelle",
]


# ============================================================================
# Query Building Utilities
# ============================================================================


def _quote_identifier(identifier: str) -> str:
    """
    Safely quote identifiers that may contain dots or reserved characters.

    Args:
        identifier: The identifier to quote

    Returns:
        Quoted identifier safe for SQL
    """
    return '"' + identifier.replace('"', '""') + '"'


def _build_where_clause(query: Optional[str]) -> Tuple[str, Dict[str, Any]]:
    """
    Create a WHERE clause for the search query and return SQL + parameters.

    Builds an OR clause that searches multiple columns for the given query.

    Args:
        query: Search query string (optional)

    Returns:
        Tuple of (SQL WHERE clause string, parameters dict)
    """
    if not query:
        return "", {}

    clauses = [
        f"LOWER(CAST({_quote_identifier(col)} AS TEXT)) LIKE :search"
        for col in SEARCHABLE_COLUMNS
    ]
    return " WHERE (" + " OR ".join(clauses) + ")", {"search": f"%{query.lower()}%"}


def search_job_offers(
    db: Session,
    query: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    """Search job offers from the database with pagination and lightweight filtering."""
    safe_page = max(page, 1)
    safe_page_size = min(max(page_size, 1), 100)
    offset = (safe_page - 1) * safe_page_size

    select_clause = ", ".join(_quote_identifier(col) for col in JOB_COLUMNS)
    table_name = _quote_identifier("offres_FT")
    where_clause, where_params = _build_where_clause(query)

    params: Dict[str, Any] = {**where_params, "limit": safe_page_size, "offset": offset}

    data_sql = f"""
        SELECT {select_clause}
        FROM {table_name}
        {where_clause}
        ORDER BY {_quote_identifier('dateActualisation')} DESC, {_quote_identifier('dateCreation')} DESC, {_quote_identifier('id')}
        LIMIT :limit OFFSET :offset
    """

    count_sql = f"SELECT COUNT(*) FROM {table_name} {where_clause}"

    rows = db.execute(text(data_sql), params).mappings().all()
    total = db.execute(text(count_sql), where_params).scalar_one()

    return {
        "results": [dict(row) for row in rows],
        "page": safe_page,
        "page_size": safe_page_size,
        "total": total,
    }
