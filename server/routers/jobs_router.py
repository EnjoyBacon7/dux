"""
Job search and France Travail API integration router.
Provides endpoints for searching job offers, loading offers from France Travail API,
and managing job-related data.
"""

import logging
import asyncio
import requests
import json
from typing import Optional, Dict, Any

from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from server.config import settings
from server.models import Fiche_Metier_ROME, User, Offres_FT
from server.database import get_db_session
from server.methods.job_search import search_job_offers
from server.methods.FT_job_search import search_france_travail
from server.thread_pool import run_blocking_in_executor
from server.dependencies import get_current_user
from services.matching_engine import MatchingEngine


from pydantic import BaseModel
from typing import Optional, Any, List, Union

def _flatten_offer(offer: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a France Travail offer object into the flat dictionary shape expected by the UI.
    
    Nested fields (entreprise, lieuTravail, salaire, contact, origineOffre, contexteTravail, agence) are exposed as top-level keys with descriptive prefixes (for example, `entreprise_nom`, `lieuTravail_libelle`, `salaire_libelle`). Missing nested keys produce `None` values for the corresponding flattened entries.
    
    Parameters:
        offer (Dict[str, Any]): The raw France Travail offer payload.
    
    Returns:
        Dict[str, Any]: A flattened offer dictionary containing original top-level fields and normalized nested attributes under prefixed keys.
    """
    entreprise = offer.get("entreprise") or {}
    lieu = offer.get("lieuTravail") or {}
    salaire = offer.get("salaire") or {}
    contact = offer.get("contact") or {}
    origine = offer.get("origineOffre") or {}
    contexte = offer.get("contexteTravail") or {}
    agence = offer.get("agence") or {}

    return {
        "id": offer.get("id"),
        "intitule": offer.get("intitule"),
        "description": offer.get("description"),
        "dateCreation": offer.get("dateCreation"),
        "dateActualisation": offer.get("dateActualisation"),
        "romeCode": offer.get("romeCode"),
        "romeLibelle": offer.get("romeLibelle"),
        "appellationlibelle": offer.get("appellationlibelle"),
        "typeContrat": offer.get("typeContrat"),
        "typeContratLibelle": offer.get("typeContratLibelle"),
        "natureContrat": offer.get("natureContrat"),
        "experienceExige": offer.get("experienceExige"),
        "experienceLibelle": offer.get("experienceLibelle"),
        "competences": offer.get("competences"),
        "dureeTravailLibelle": offer.get("dureeTravailLibelle"),
        "dureeTravailLibelleConverti": offer.get("dureeTravailLibelleConverti"),
        "alternance": offer.get("alternance"),
        "nombrePostes": offer.get("nombrePostes"),
        "accessibleTH": offer.get("accessibleTH"),
        "qualificationCode": offer.get("qualificationCode"),
        "qualificationLibelle": offer.get("qualificationLibelle"),
        "codeNAF": offer.get("codeNAF"),
        "secteurActivite": offer.get("secteurActivite"),
        "secteurActiviteLibelle": offer.get("secteurActiviteLibelle"),
        "offresManqueCandidats": offer.get("offresManqueCandidats"),
        "entrepriseAdaptee": offer.get("entrepriseAdaptee"),
        "employeurHandiEngage": offer.get("employeurHandiEngage"),
        "lieuTravail_libelle": lieu.get("libelle"),
        "lieuTravail_latitude": lieu.get("latitude"),
        "lieuTravail_longitude": lieu.get("longitude"),
        "lieuTravail_codePostal": lieu.get("codePostal"),
        "lieuTravail_commune": lieu.get("commune"),
        "entreprise_nom": entreprise.get("nom"),
        "entreprise_entrepriseAdaptee": entreprise.get("entrepriseAdaptee"),
        "salaire_libelle": salaire.get("libelle"),
        "salaire_complement1": salaire.get("complement1"),
        "salaire_listeComplements": salaire.get("listeComplements"),
        "contact_nom": contact.get("nom"),
        "contact_coordonnees1": contact.get("coordonnees1"),
        "contact_coordonnees2": contact.get("coordonnees2"),
        "contact_coordonnees3": contact.get("coordonnees3"),
        "contact_courriel": contact.get("courriel"),
        "contact_urlPostulation": contact.get("urlPostulation"),
        "contact_telephone": contact.get("telephone"),
        "origineOffre_origine": origine.get("origine"),
        "origineOffre_urlOrigine": origine.get("urlOrigine"),
        "contexteTravail_horaires": contexte.get("horaires"),
        "contexteTravail_conditionsExercice": contexte.get("conditionsExercice"),
        "formations": offer.get("formations"),
        "qualitesProfessionnelles": offer.get("qualitesProfessionnelles"),
        "langues": offer.get("langues"),
        "permis": offer.get("permis"),
        "entreprise_logo": entreprise.get("logo"),
        "entreprise_description": entreprise.get("description"),
        "entreprise_url": entreprise.get("url"),
        "agence_courriel": agence.get("courriel"),
        "salaire_commentaire": salaire.get("commentaire"),
        "deplacementCode": offer.get("deplacementCode"),
        "deplacementLibelle": offer.get("deplacementLibelle"),
        "trancheEffectifEtab": offer.get("trancheEffectifEtab"),
        "experienceCommentaire": offer.get("experienceCommentaire"),
    }

# ============================================================================
# Router Setup
# ============================================================================


router = APIRouter(prefix="/jobs", tags=["Jobs"])
logger = logging.getLogger(__name__)

# ============================================================================
# Job Search Endpoints
# ============================================================================


@router.get("/search", summary="Search job offers from db")
def search_jobs(
    q: str = Query(None, description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    db: Session = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Perform a text search for job offers in the local database with pagination.
    
    Returns:
        dict: Search result payload containing:
            - `results` (list): Matched job offers (possibly empty).
            - `page` (int): Current page number.
            - `page_size` (int): Number of results per page.
            - `total` (int): Total number of matching offers.
            On error, includes an `error` (str) key and returns `results` as an empty list with `total` set to 0.
    """
    try:
        result = search_job_offers(db, query=q, page=page, page_size=page_size)
        return result
    except Exception as e:
        logger.error(f"Error searching jobs: {e}")
        return {"error": str(e), "results": [], "page": page, "page_size": page_size, "total": 0}


@router.post("/load_offers", summary="Load offers from France Travail API")
async def load_offers(
    nb_offres: int = Query(150, description="Nombre d'offres à récupérer"),
    # ... (Je garde tous tes paramètres existants pour ne rien casser) ...
    accesTravailleurHandicape: bool = Query(None),
    appellation: str = Query(None),
    codeNAF: str = Query(None),
    codeROME: str = Query(None),
    commune: str = Query(None),
    departement: str = Query(None),
    distance: int = Query(None),
    domaine: str = Query(None),
    dureeContratMax: str = Query(None),
    dureeContratMin: str = Query(None),
    dureeHebdo: str = Query(None),
    dureeHebdoMax: str = Query(None),
    dureeHebdoMin: str = Query(None),
    employeursHandiEngages: bool = Query(None),
    entreprisesAdaptees: bool = Query(None),
    experience: str = Query(None),
    experienceExigence: str = Query(None),
    grandDomaine: str = Query(None),
    inclureLimitrophes: bool = Query(None),
    maxCreationDate: str = Query(None),
    minCreationDate: str = Query(None),
    modeSelectionPartenaires: str = Query(None),
    motsCles: str = Query(None),
    natureContrat: str = Query(None),
    niveauFormation: str = Query(None),
    offresMRS: bool = Query(None),
    offresManqueCandidats: bool = Query(None),
    origineOffre: int = Query(None),
    partenaires: str = Query(None),
    paysContinent: str = Query(None),
    periodeSalaire: str = Query(None),
    permis: str = Query(None),
    publieeDepuis: int = Query(None),
    qualification: str = Query(None),
    content_range: str = Query(None, alias="range"),
    region: str = Query(None),
    salaireMin: str = Query(None),
    secteurActivite: str = Query(None),
    sort: str = Query(None),
    tempsPlein: bool = Query(None),
    theme: str = Query(None),
    typeContrat: str = Query(None),
):
    """
    Load job offers from the France Travail API and return them in the flat shape expected by the UI.
    
    Builds request parameters from the function arguments, maps the `content_range` alias to the `range` parameter sent to the France Travail API, and fetches up to `nb_offres` results. When the API returns a list of offers each offer is normalized with the module's flattening logic before being returned.
    
    Parameters:
        content_range (str): If present, this value is sent as the `range` parameter to the France Travail API.
    
    Returns:
        list[dict]: A list of normalized (flattened) offer dictionaries when the API returns multiple offers.
        dict: The raw API response when it is not a list, or an error object like `{"error": "<message>"}` on failure.
    """
    try:
        # Reconstitution du dictionnaire de paramètres (simplifié pour la lecture)
        # On récupère tous les arguments locaux sauf ceux techniques
        ft_parameters = locals().copy()
        keys_to_exclude = ['nb_offres', 'content_range']
        ft_parameters = {k: v for k, v in ft_parameters.items() if k not in keys_to_exclude and v is not None}
        
        # Mapping spécifique pour 'range' qui s'appelait content_range
        if content_range:
            ft_parameters["range"] = content_range

        offers = await run_blocking_in_executor(
            search_france_travail,
            ft_parameters,
            nb_offres
        )
        if isinstance(offers, list):
            return [_flatten_offer(offer) for offer in offers]
        return offers

    except ValueError as e:
        logger.error(f"Error loading offers: {str(e)}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error loading offers: {e}")
        return {"error": str(e)}


@router.post("/load_fiche_metier", summary="Load fiche metier from France Travail API (ROME)")
def load_fiche_metier():
    """
    Load ROME "fiche métier" data from the France Travail API into the database.
    
    Obtains an OAuth token using client credentials from settings, retrieves fiche métier records from the configured API, truncates the Fiche_Metier_ROME table, and inserts the fetched records (serializing nested structures as JSON where needed). Any insertion errors for individual items are ignored; the entire operation returns a summary or an error payload.
    
    Returns:
        dict: On success, {"message": "<n> fiches métiers ROME chargées."} where <n> is the number of records fetched.
              On failure, {"error": "<error message>"} with the caught exception message.
    """
    try:
        CLIENT_ID = settings.client_id
        CLIENT_SECRET = settings.client_secret
        AUTH_URL = settings.auth_url
        API_URL_FICHE_METIER = settings.api_url_fiche_metier
        DATABASE_URL = settings.database_url

        data = {
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scope": f"api_rome-fiches-metiersv1 nomenclatureRome",
        }
        params = {"realm": "/partenaire"}

        resp = requests.post(AUTH_URL, data=data, params=params)
        resp.raise_for_status()
        token = resp.json()["access_token"]

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }

        resp = requests.get(API_URL_FICHE_METIER, headers=headers)
        resp.raise_for_status()
        fiche_metier = resp.json()

        logger.info(f"Récupération des fiches métiers : {len(fiche_metier)} obtenues.")

        # Utilisation d'un engine dédié ici (comme dans ton code original)
        # Note: Idéalement, il faudrait utiliser `db: Session = Depends(get_db_session)`
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        session.execute(text("TRUNCATE TABLE Fiche_Metier_ROME RESTART IDENTITY CASCADE;"))
        session.commit()

        try:
            for fiche in fiche_metier:
                # Ajout de json.dumps pour éviter les erreurs d'insertion de listes/dicts
                fiche_insert = Fiche_Metier_ROME(
                    code=fiche.get("code"),
                    metier=json.dumps(fiche.get("metier")), 
                    groupesCompetencesMobilisees=json.dumps(fiche.get("groupesCompetencesMobilisees")),
                    groupesSavoirs=json.dumps(fiche.get("groupesSavoirs"))
                )
                try:
                    session.add(fiche_insert)
                except:
                    pass
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Erreur sauvegarde ROME : {e}")
        finally:
            session.close()

        return {"message": f"{len(fiche_metier)} fiches métiers ROME chargées."}

    except Exception as e:
        return {"error": str(e)}


# ============================================================================
#  Analyse IA
# ============================================================================

@router.get("/analyze/{job_id}")
async def analyze_specific_job(
    job_id: str, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Compute a compatibility score between the authenticated user and a specific job offer.
    
    Parameters:
        job_id (str): Identifier of the job offer to analyze.
    
    Returns:
        dict: Payload containing:
            - status: "success" on successful analysis.
            - candidat: object with `nom` (full name) and `titre` (headline) of the user.
            - job: object with `id`, `intitule`, and `entreprise` of the offer.
            - analysis: evaluation result produced by the matching engine.
    
    Raises:
        HTTPException: 404 if the job offer is not found.
        HTTPException: 500 if an error occurs during analysis.
    """
    
    # 1. Vérifier l'offre dans la base locale
    offre = db.query(Offres_FT).filter(Offres_FT.id == job_id).first()
    
    if not offre:
        raise HTTPException(status_code=404, detail="Offre introuvable")

    logger.info(f" Analyse demandée par : {current_user.username} pour l'offre {offre.id}")

    # 2. Initialiser le moteur
    engine = MatchingEngine(db)
    
    try:
        # 3. Lancer l'analyse (non-bloquante)
        evaluation = await asyncio.to_thread(engine.analyser_match, current_user, offre)
        
        return {
            "status": "success",
            "candidat": {
                "nom": f"{current_user.first_name} {current_user.last_name}",
                "titre": current_user.headline
            },
            "job": {
                "id": offre.id,
                "intitule": offre.intitule,
                "entreprise": offre.entreprise_nom
            },
            "analysis": evaluation
        }
        
    except Exception as e:
        logger.error(f"Erreur critique lors de l'analyse : {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
# ============================================================================
# NOUVELLE ROUTE : Analyse IA DIRECTE (Sans DB)
# ============================================================================

# Modèle pour valider les données reçues du Frontend
class JobDataForAnalysis(BaseModel):
    id: str
    intitule: Optional[str] = None
    description: Optional[str] = None
    entreprise_nom: Optional[str] = None
    competences: Optional[Any] = None # Peut être une liste, un dict ou une string

@router.post("/analyze")
async def analyze_job_direct(
    job_data: JobDataForAnalysis, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Perform an on-demand AI matching analysis for a provided job payload without reading from the database.
    
    The function constructs a virtual job object from `job_data`, runs the MatchingEngine analysis using the authenticated `current_user`, and returns a structured result containing the candidate's name and title, the job's id/intitule/entreprise, and the analysis evaluation.
    
    Returns:
        dict: A payload with keys:
            - "status": "success" on successful analysis.
            - "candidat": dict with "nom" (full name) and "titre" (headline) of the current user.
            - "job": dict with "id", "intitule", and "entreprise" from the provided job data.
            - "analysis": the evaluation result produced by the MatchingEngine.
    
    Raises:
        HTTPException: with status code 500 and the error detail if the analysis fails.
    """
    logger.info(f" Analyse directe demandée par : {current_user.username} pour l'offre {job_data.id}")

    # 1. On crée un objet "virtuel" Offres_FT pour que le MatchingEngine puisse le lire
    # On convertit les compétences en string si nécessaire pour le prompt
    comps = job_data.competences
    if isinstance(comps, (list, dict)):
        import json
        comps = json.dumps(comps)

    offre_virtuelle = Offres_FT(
        id=job_data.id,
        intitule=job_data.intitule,
        description=job_data.description,
        entreprise_nom=job_data.entreprise_nom,
        competences=comps
    )

    # 2. Initialiser le moteur
    engine = MatchingEngine(db)
    
    try:
        # 3. Lancer l'analyse (non-bloquante)
        evaluation = await asyncio.to_thread(engine.analyser_match, current_user, offre_virtuelle)
        
        return {
            "status": "success",
            "candidat": {
                "nom": f"{current_user.first_name} {current_user.last_name}",
                "titre": current_user.headline
            },
            "job": {
                "id": job_data.id,
                "intitule": job_data.intitule,
                "entreprise": job_data.entreprise_nom
            },
            "analysis": evaluation
        }
        
    except Exception as e:
        logger.error(f" Erreur critique lors de l'analyse : {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))