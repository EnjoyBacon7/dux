"""
Job search and France Travail API integration router.

Provides endpoints for searching job offers, loading offers from France Travail API,
and managing job-related data.
"""

import logging
import requests
import json
from typing import Optional, Dict, Any, List, Union

from fastapi import APIRouter, Query, Depends
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from server.config import settings
from server.models import Fiche_Metier_ROME, User, Offres_FT
from server.database import get_db_session
from server.methods.job_search import search_job_offers
from server.methods.FT_job_search import search_france_travail
from server.thread_pool import run_blocking_in_executor
from server.dependencies import get_current_user
from server.methods.matching_engine import MatchingEngine
import asyncio



from pydantic import BaseModel
from fastapi import HTTPException

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

    Performs full-text search across job titles, descriptions, locations,
    company names, and other relevant fields.

    Args:
        q: Search query string
        page: Page number for pagination (default: 1)
        page_size: Number of results per page (default: 20, max: 100)
        db: Database session

    Returns:
        dict: Search results with pagination info and list of matching offers

    Raises:
        Returns error dict if search fails
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
    accesTravailleurHandicape: bool = Query(None, description="Offres ouvertes aux Bénéficiaires de l'Obligation d'Emploi"),
    appellation: str = Query(None, description="Code appellation ROME de l'offre"),
    codeNAF: str = Query(None, description="Code NAF (Code APE) de l'offre"),
    codeROME: str = Query(None, description="Code ROME de l'offre"),
    commune: str = Query(None, description="Code INSEE de la commune"),
    departement: str = Query(None, description="Département de l'offre"),
    distance: int = Query(None, description="Distance kilométrique du rayon de la recherche autour de la commune"),
    domaine: str = Query(None, description="Domaine de l'offre"),
    dureeContratMax: str = Query(None, description="Durée de contrat maximale (en mois)"),
    dureeContratMin: str = Query(None, description="Durée de contrat minimale (en mois)"),
    dureeHebdo: str = Query(None, description="Type de durée du contrat de l'offre"),
    dureeHebdoMax: str = Query(None, description="Durée hebdomadaire maximale (format HHMM)"),
    dureeHebdoMin: str = Query(None, description="Durée hebdomadaire minimale (format HHMM)"),
    employeursHandiEngages: bool = Query(None, description="Filtre les offres dont l'employeur est reconnu pour ses actions en faveur du handicap"),
    entreprisesAdaptees: bool = Query(None, description="Filtre les offres dont l'entreprise permet des conditions adaptées au handicap"),
    experience: str = Query(None, description="Niveau d'expérience demandé"),
    experienceExigence: str = Query(None, description="Exigence d'expérience"),
    grandDomaine: str = Query(None, description="Code du grand domaine de l'offre"),
    inclureLimitrophes: bool = Query(None, description="Inclure les départements limitrophes dans la recherche"),
    maxCreationDate: str = Query(None, description="Date maximale pour laquelle rechercher des offres"),
    minCreationDate: str = Query(None, description="Date minimale pour laquelle rechercher des offres"),
    modeSelectionPartenaires: str = Query(None, description="Mode de sélection des partenaires"),
    motsCles: str = Query(None, description="Mots clés pour la recherche"),
    natureContrat: str = Query(None, description="Code de la nature du contrat"),
    niveauFormation: str = Query(None, description="Niveau de formation demandé"),
    offresMRS: bool = Query(None, description="Uniquement les offres avec méthode de recrutement par simulation"),
    offresManqueCandidats: bool = Query(None, description="Filtre les offres difficiles à pourvoir"),
    origineOffre: int = Query(None, description="Origine de l'offre"),
    partenaires: str = Query(None, description="Liste des codes partenaires à inclure ou exclure"),
    paysContinent: str = Query(None, description="Pays ou continent de l'offre"),
    periodeSalaire: str = Query(None, description="Période pour le calcul du salaire minimum"),
    permis: str = Query(None, description="Permis demandé"),
    publieeDepuis: int = Query(None, description="Recherche les offres publiées depuis maximum X jours"),
    qualification: str = Query(None, description="Qualification du poste"),
    content_range: str = Query(None, description="Pagination des données"),
    region: str = Query(None, description="Région de l'offre"),
    salaireMin: str = Query(None, description="Salaire minimum recherché"),
    secteurActivite: str = Query(None, description="Division NAF de l'offre"),
    sort: str = Query(None, description="Tri des résultats"),
    tempsPlein: bool = Query(None, description="Temps plein ou partiel"),
    theme: str = Query(None, description="Thème ROME du métier"),
    typeContrat: str = Query(None, description="Code du type de contrat"),
):
    """
    Charge des données depuis l'API France Travail en fonction des paramètres de recherche.
    """
    try:
        # Build FT parameters dictionary
        ft_parameters = {
            "accesTravailleurHandicape": accesTravailleurHandicape,
            "appellation": appellation,
            "codeNAF": codeNAF,
            "codeROME": codeROME,
            "commune": commune,
            "departement": departement,
            "distance": distance,
            "domaine": domaine,
            "dureeContratMax": dureeContratMax,
            "dureeContratMin": dureeContratMin,
            "dureeHebdo": dureeHebdo,
            "dureeHebdoMax": dureeHebdoMax,
            "dureeHebdoMin": dureeHebdoMin,
            "employeursHandiEngages": employeursHandiEngages,
            "entreprisesAdaptees": entreprisesAdaptees,
            "experience": experience,
            "experienceExigence": experienceExigence,
            "grandDomaine": grandDomaine,
            "inclureLimitrophes": inclureLimitrophes,
            "maxCreationDate": maxCreationDate,
            "minCreationDate": minCreationDate,
            "modeSelectionPartenaires": modeSelectionPartenaires,
            "motsCles": motsCles,
            "natureContrat": natureContrat,
            "niveauFormation": niveauFormation,
            "offresMRS": offresMRS,
            "offresManqueCandidats": offresManqueCandidats,
            "origineOffre": origineOffre,
            "partenaires": partenaires,
            "paysContinent": paysContinent,
            "periodeSalaire": periodeSalaire,
            "permis": permis,
            "publieeDepuis": publieeDepuis,
            "qualification": qualification,
            "range": content_range,
            "region": region,
            "salaireMin": salaireMin,
            "secteurActivite": secteurActivite,
            "sort": sort,
            "tempsPlein": tempsPlein,
            "theme": theme,
            "typeContrat": typeContrat,
        }

        # Use centralized search method in thread pool to avoid blocking other clients
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
    Charge des données depuis l'API France Travail en fonction des paramètres de recherche.
    """

    try:
        CLIENT_ID = settings.client_id
        CLIENT_SECRET = settings.client_secret
        AUTH_URL = settings.auth_url
        API_URL_FICHE_METIER = settings.api_url_fiche_metier
        DATABASE_URL = settings.database_url

        """
        Récupère un token OAuth2 en mode client_credentials.
        """
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

        # Récupérer les offres depuis l'API
        fiche_metier = []

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }

        try:
            resp = requests.get(API_URL_FICHE_METIER, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except:
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
            data = resp.json()

        fiche_metier += data

        logger = logging.getLogger("uvicorn.info")
        logger.info(f"Récupération des fiches métiers : {len(fiche_metier)} obtenues.")
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)

        if not fiche_metier:
            print("Aucune offre reçue, rien à sauvegarder.")
            return

        session = Session()
        session.execute(text("TRUNCATE TABLE Fiche_Metier_ROME RESTART IDENTITY CASCADE;"))
        session.commit()

        try:
            for fiche in fiche_metier:
                fiche_insert = Fiche_Metier_ROME(
                    code=fiche.get("code"),
                    metier=fiche.get("metier"),  # {code, libelle}
                    groupesCompetencesMobilisees=fiche.get(
                        "groupesCompetencesMobilisees"),  # Array of competency groups
                    groupesSavoirs=fiche.get("groupesSavoirs")  # Array of knowledge groups
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
            logger.error(f"Erreur lors de la sauvegarde des fiches métiers ROME : {str(e)}", exc_info=True)
        finally:
            session.close()

        return {"message": f"{len(fiche_metier)} fiches métiers ROME chargées et sauvegardées avec succès"}

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
    
    logger.info(f"Analyse directe demandée par : {current_user.username} pour l'offre {job_data.id}")

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