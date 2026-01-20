"""
Job search and France Travail API integration router.
Provides endpoints for searching job offers, loading offers from France Travail API,
and managing job-related data.
"""

import logging
import asyncio
import requests
import json
from typing import Optional, Dict, Any, List, Union

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

def _flatten_offer(offer: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize France Travail offers to the flat shape expected by the UI."""
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
    Search job offers from the local database with text search and pagination.
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
    Charge des données depuis l'API France Travail.
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
    Charge des données depuis l'API France Travail (ROME).
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

        resp = requests.get(API_URL_FICHE_METIER, headers=headers, timeout=30)
        resp.raise_for_status()
        fiche_metier = resp.json()

        logger.info(f"Récupération des fiches métiers : {len(fiche_metier)} obtenues.")
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
                except Exception as e:
                    # On loggue l'erreur avec la stack trace complète et l'ID de la fiche
                    logger.exception(f"Erreur lors de l'ajout de la fiche {fiche.get('code')}: {e}")
                    # On continue la boucle pour traiter les fiches suivantes
                    continue

            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Erreur globale lors de la transaction ROME : {e}")
        finally:
            session.close()

        return {"message": f"{len(fiche_metier)} fiches métiers ROME chargées."}

    except Exception as e:
        return {"error": str(e)}


# ============================================================================
#  Analyse IA (Helpers & Routes)
# ============================================================================

def _run_analysis_in_thread(
    user_id: int,
    job_id: Optional[str],
    job_payload: Optional[Dict[str, Any]],
    bind,
):
    """
    Fonction exécutée dans un thread séparé.
    Elle crée sa propre session DB à partir du 'bind' (Engine) pour éviter
    les erreurs de type DetachedInstanceError avec les objets ORM.
    """
    # On crée une nouvelle session dédiée à ce thread
    SessionLocal = sessionmaker(bind=bind)
    with SessionLocal() as session:
        # On recharge l'utilisateur "frais" depuis la DB
        user = session.get(User, user_id)
        if not user:
            raise ValueError("Utilisateur introuvable dans le thread")

        # Soit on cherche l'offre en DB, soit on la crée depuis le payload
        if job_payload is None:
            # Cas Analyse par ID (GET)
            job = session.query(Offres_FT).filter(Offres_FT.id == job_id).first()
            if not job:
                raise ValueError("Offre introuvable dans le thread")
        else:
            # Cas Analyse Directe (POST)
            # On recrée l'objet temporaire
            # Gestion des compétences pour qu'elles soient en string JSON si besoin
            comps = job_payload.get('competences')
            if isinstance(comps, (list, dict)):
                comps = json.dumps(comps)
            
            job = Offres_FT(
                id=job_payload.get('id'),
                intitule=job_payload.get('intitule'),
                description=job_payload.get('description'),
                entreprise_nom=job_payload.get('entreprise_nom'),
                competences=comps
            )

        # On lance le moteur avec cette session locale au thread
        engine = MatchingEngine(session)
        return engine.analyser_match(user, job)


@router.get("/analyze/{job_id}")
async def analyze_specific_job(
    job_id: str, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Analyse "On-Demand" via DB (Thread-Safe).
    """
    # On récupère le 'bind' (la connexion moteur) pour la passer au thread
    bind = db.get_bind()
    user_id = current_user.id

    logger.info(f" Analyse demandée par : {current_user.username} pour l'offre {job_id}")

    try:
        # On lance l'analyse dans un thread en passant uniquement des IDs et le bind
        evaluation = await asyncio.to_thread(
            _run_analysis_in_thread,
            user_id,
            job_id,
            None, # Pas de payload, on utilise l'ID
            bind
        )
        
        # Pour la réponse HTTP, on peut utiliser la session normale du routeur
        # pour récupérer les infos basiques
        offre = db.query(Offres_FT).filter(Offres_FT.id == job_id).first()
        
        return {
            "status": "success",
            "candidat": {
                "nom": f"{current_user.first_name} {current_user.last_name}",
                "titre": current_user.headline
            },
            "job": {
                "id": job_id,
                "intitule": offre.intitule if offre else "N/A",
                "entreprise": offre.entreprise_nom if offre else "N/A"
            },
            "analysis": evaluation
        }
        
    except Exception as e:
        logger.error(f"Erreur critique lors de l'analyse : {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class JobDataForAnalysis(BaseModel):
    id: str
    intitule: Optional[str] = None
    description: Optional[str] = None
    entreprise_nom: Optional[str] = None
    competences: Optional[Any] = None

@router.post("/analyze")
async def analyze_job_direct(
    job_data: JobDataForAnalysis, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Analyse directe (Thread-Safe).
    """
    bind = db.get_bind()
    user_id = current_user.id
    
    logger.info(f"🎯 Analyse directe demandée par : {current_user.username} pour l'offre {job_data.id}")

    try:
        # On prépare le payload sous forme de dict simple
        payload = job_data.model_dump() # ou .dict()

        evaluation = await asyncio.to_thread(
            _run_analysis_in_thread,
            user_id,
            None, # Pas d'ID DB
            payload, # On fournit le payload
            bind
        )
        
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
        logger.error(f"Erreur critique lors de l'analyse directe : {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))