"""
Job search and France Travail API integration router.

Provides endpoints for searching job offers, loading offers from France Travail API,
and managing job-related data.
"""

import logging
import requests
import re

from fastapi import APIRouter, Query, Depends
from server.config import settings
from server.models import Metier_ROME, User, Offres_FT
from server.database import get_db_session
from server.methods.job_search import search_job_offers
import json
from typing import Optional, Dict, Any, List, Union, Tuple

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from tqdm.auto import tqdm

from server.methods.FT_job_search import search_france_travail
from server.thread_pool import run_blocking_in_executor
from server.dependencies import get_current_user
from server.methods.matching_engine import MatchingEngine
import asyncio

from pydantic import BaseModel
from fastapi import HTTPException


def get_token_api_FT(CLIENT_ID: str, CLIENT_SECRET: str, AUTH_URL: str, scope: str) -> str:
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": scope
    }
    params = {"realm": "/partenaire"}

    resp = requests.post(AUTH_URL, data=data, params=params, timeout = 30)
    resp.raise_for_status()
    token = resp.json()["access_token"]

    return token

def get_offers(code_rome: str) -> dict:
    FT_CLIENT_ID = settings.ft_client_id
    FT_CLIENT_SECRET = settings.ft_client_secret
    FT_AUTH_URL = settings.ft_auth_url
    FT_API_OFFRES_URL = settings.ft_api_url_offres

    # Récupère un token OAuth2 en mode client_credentials.

    token = get_token_api_FT(FT_CLIENT_ID, FT_CLIENT_SECRET, FT_AUTH_URL, "api_offresdemploiv2 o2dsoffre")

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    resultat = []
    # Getting the list of offers for the given ROME code
    page = 0
    while len(resultat) % 150 == 0 and page < 20:
        try:
            resp = requests.get(FT_API_OFFRES_URL + f"?codeROME={code_rome}&range={page * 150}-{page * 150 + 149}", headers=headers, timeout=30)
            resp.raise_for_status()
        except:
            token = get_token_api_FT(FT_CLIENT_ID, FT_CLIENT_SECRET, FT_AUTH_URL, "api_offresdemploiv2 o2dsoffre")

            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            resp = requests.get(FT_API_OFFRES_URL + f"?codeROME={code_rome}&range={page * 150}-{page * 150 + 149}", headers=headers, timeout=30)
            resp.raise_for_status()

        try:
            data = resp.json()
        except:
            data = {"resultats": []}
        
        if len(data.get("resultats", [])) == 0:
            break

        resultat += data.get("resultats", [])
        page += 1

    return resultat


def _to_float(s: str) -> float:
    return float(s.replace(",", "."))


def _match_first(text: str, patterns: list[str]) -> re.Match:
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            return m
    raise ValueError("Format non reconnu")


def _parse_amounts_and_months(text: str, prefix: str) -> Tuple[float, float]:
    """
    Returns (amount, nb_mois) where amount is:
      - the single amount, or
      - the average of (inf, sup) if a range is provided.

    nb_mois defaults to 12.0 when not provided.
    """
    patterns = [
        # range + months
        rf"{prefix}\s+de\s+([\d.,]+)\s*Euros\s+à\s+([\d.,]+)\s*Euros\s+sur\s+([\d.,]+)\s*mois",
        # range
        rf"{prefix}\s+de\s+([\d.,]+)\s*Euros\s+à\s+([\d.,]+)\s*Euros",
        # single + months
        rf"{prefix}\s+de\s+([\d.,]+)\s*Euros\s+sur\s+([\d.,]+)\s*mois",
        # single
        rf"{prefix}\s+de\s+([\d.,]+)\s*Euros",
    ]

    m = _match_first(text, patterns)

    # Determine which case matched by number of captured groups
    if m.lastindex == 3:
        inf_ = _to_float(m.group(1))
        sup_ = _to_float(m.group(2))
        nb_mois = _to_float(m.group(3))
        amount = (inf_ + sup_) / 2.0
    elif m.lastindex == 2:
        # Could be range (inf, sup) OR single+months (amount, months)
        # Disambiguate via presence of "à" in the matched text.
        if "à" in m.group(0).lower():
            inf_ = _to_float(m.group(1))
            sup_ = _to_float(m.group(2))
            amount = (inf_ + sup_) / 2.0
            nb_mois = 12.0
        else:
            amount = _to_float(m.group(1))
            nb_mois = _to_float(m.group(2))
    elif m.lastindex == 1:
        amount = _to_float(m.group(1))
        nb_mois = 12.0
    else:
        raise ValueError("Format non reconnu")

    return amount, nb_mois


def _parse_nb_heures_semaine(texte_heure: Optional[str]) -> float:
    """
    Extract weekly hours; default to 35.0 if not found/parsable.
    (No exceptions used for control flow.)
    """
    if not texte_heure:
        return 35.0

    # Keep your behavior: cut anything after "semaine"
    texte_heure = re.sub(r"(semaine)\b.*$", r"\1", texte_heure, flags=re.S | re.IGNORECASE)

    # Temps partiel - XXH/semaine
    m = re.search(r"Temps\s+partiel\s+-\s+([\d.,]+)H/semaine\b", texte_heure, flags=re.IGNORECASE)
    if m:
        return _to_float(m.group(1))

    # XXHYY/semaine (e.g., 35H30/semaine)
    m = re.search(r"([\d.,]+)H([\d.,]+)/semaine\b", texte_heure, flags=re.IGNORECASE)
    if m:
        heures = _to_float(m.group(1))
        minutes = _to_float(m.group(2))
        return heures + minutes / 60.0

    # XXH/semaine
    m = re.search(r"([\d.,]+)H/semaine\b", texte_heure, flags=re.IGNORECASE)
    if m:
        return _to_float(m.group(1))

    return 35.0


def _parse_mensuel(texte_salaire: str) -> float:
    salaire_mensuel, nb_mois = _parse_amounts_and_months(texte_salaire, "Mensuel")
    annuel = salaire_mensuel * nb_mois
    return annuel / 12.0


def _parse_annuel(texte_salaire: str) -> float:
    salaire_annuel, nb_mois = _parse_amounts_and_months(texte_salaire, "Annuel")
    annuel_effectif = salaire_annuel * (nb_mois / 12.0)
    return annuel_effectif / 12.0


def _parse_horaire(texte_salaire: str, texte_heure: Optional[str]) -> float:
    salaire_horaire, nb_mois = _parse_amounts_and_months(texte_salaire, "Horaire")
    nb_heures_semaine = _parse_nb_heures_semaine(texte_heure)
    annuel = salaire_horaire * nb_heures_semaine * 52.0 * (nb_mois / 12.0)
    return annuel / 12.0


def calcul_salaire(texte_salaire: Optional[str], texte_heure: Optional[str]) -> Optional[float]:
    """
    Returns monthly salary as float, or None if salary text cannot be parsed.

    Top-level catches only (ValueError, AttributeError) as requested.
    """
    if not texte_salaire:
        return None

    ts = texte_salaire.strip()

    dispatch = {
        "mensuel": lambda: _parse_mensuel(ts),
        "horaire": lambda: _parse_horaire(ts, texte_heure),
        "annuel":  lambda: _parse_annuel(ts),
    }

    try:
        key = ts[:7].strip().lower()  # "Mensuel", "Horaire", "Annuel"
        handler = dispatch.get(key)
        return handler() if handler else None

    except (ValueError, AttributeError) as e:
        # Keep logs helpful; let unexpected exceptions bubble up.
        logger.info("calcul_salaire: parsing failed for texte_salaire=%r: %s", texte_salaire, e)
        return None


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
        FT_CLIENT_ID = settings.ft_client_id
        FT_CLIENT_SECRET = settings.ft_client_secret
        FT_AUTH_URL = settings.ft_auth_url
        FT_API_URL_CODE_METIER = settings.ft_api_url_code_metier
        FT_API_URL_METIER = settings.ft_api_url_fiche_metier
        DATABASE_URL = settings.database_url

        """
        Récupère un token OAuth2 en mode client_credentials.
        """

        token = get_token_api_FT(FT_CLIENT_ID, FT_CLIENT_SECRET, FT_AUTH_URL, "api_rome-metiersv1 nomenclatureRome")

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }

        # Récupérer les codes métiers ROME
        code_metier = []

        # Getting the list of ROME codes
        try:
            resp = requests.get(FT_API_URL_CODE_METIER, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except:
            token = get_token_api_FT(FT_CLIENT_ID, FT_CLIENT_SECRET, FT_AUTH_URL, "api_rome-metiersv1 nomenclatureRome")
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            resp = requests.get(FT_API_URL_CODE_METIER, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()

        code_metier += data

        print(f"Nombre de codes ROME récupérés : {len(code_metier)}")

        token = get_token_api_FT(FT_CLIENT_ID, FT_CLIENT_SECRET, FT_AUTH_URL, "api_rome-metiersv1 nomenclatureRome")

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }

        fiche_metier = []
        
        champs = "?champs=accesemploi,appellations(code,classification,libelle),centresinteretslies(centreinteret(libelle,code,definition)),code,libelle,competencesmobilisees(libelle,code),contextestravail(libelle,code,categorie),definition,domaineprofessionnel(libelle,code,granddomaine(libelle,code)),metiersenproximite(libelle,code),secteursactiviteslies(secteuractivite(libelle,code,secteuractivite(libelle,code,definition),definition)),themes(libelle,code),emploicadre,emploireglemente,transitiondemographique,transitionecologique,transitionnumerique"

        for code in tqdm(code_metier):
            try:
                while True:
                    resp = requests.get(FT_API_URL_METIER + f"/{code.get("code")}" + champs, headers=headers, timeout=30)
                    if resp.status_code != 429:
                        break
                
                resp.raise_for_status()
                data = resp.json()
                # Getting offers info from france travail API
                liste_offres = get_offers(code.get("code"))
                salaire = []
                for offre in liste_offres:
                    salaire.append(calcul_salaire(str(offre.get('salaire').get('libelle')), str(offre.get('dureeTravailLibelle'))))
                
            except:
                token = get_token_api_FT(FT_CLIENT_ID, FT_CLIENT_SECRET, FT_AUTH_URL, "api_rome-metiersv1 nomenclatureRome")
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json"
                }
                while True:
                    resp = requests.get(FT_API_URL_METIER + f"/{code.get("code")}" + champs, headers=headers, timeout=30)
                    if resp.status_code != 429:
                        break
                
                resp.raise_for_status()
                data = resp.json()

                # Getting offers info from france travail API
                liste_offres = get_offers(code.get("code"))
                salaire = []
                for offre in liste_offres:
                    salaire.append(calcul_salaire(str(offre.get("salaire").get('libelle')), str(offre.get('dureeTravailLibelle'))))

            if len(liste_offres) == 0:
                data['nb_offre'] = 0
                data['liste_salaire_offre'] = []
            else:
                data['nb_offre'] = len(liste_offres)
                data['liste_salaire_offre'] = salaire

            fiche_metier.append(data.copy())


        logger = logging.getLogger("uvicorn.info")
        logger.info(f"Récupération des fiches métiers : {len(fiche_metier)} obtenues.")
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)

        if not fiche_metier:
            print("Aucune fiche métier reçue, rien à sauvegarder.")
            return

        session = Session()
        session.execute(text("TRUNCATE TABLE Metier_ROME RESTART IDENTITY CASCADE;"))
        session.commit()

        try:
            for fiche in fiche_metier:
                fiche_insert = Metier_ROME(
                    code = fiche.get("code"),
                    libelle = fiche.get("libelle"),
                    accesEmploi = fiche.get("accesEmploi"),
                    appellations = fiche.get("appellations"),  # Array of appellations
                    centresInteretsLies = fiche.get("centresInteretsLies"),  # Array of related interest centers
                    competencesMobilisees = fiche.get("competencesMobilisees"),  # Array of skills
                    contextesTravail = fiche.get("contextesTravail"),  # Array of work contexts
                    definition = fiche.get("definition"),
                    domaineProfessionnel = fiche.get("domaineProfessionnel"),
                    metiersEnProximite = fiche.get("metiersEnProximite"),
                    secteursActivitesLies = fiche.get("secteursActivitesLies"),
                    themes = fiche.get("themes"),  # Array of themes
                    transitionEcologique = fiche.get("transitionEcologique"),  # Ecological transition info
                    transitionNumerique = fiche.get("transitionNumerique"),  # Digital transition info
                    transitionDemographique = fiche.get("transitionDemographique"),  # Demographic transition info
                    emploiCadre = fiche.get("emploiCadre"),
                    emploiReglemente = fiche.get("emploiReglemente"),
                    nb_offre = fiche.get("nb_offre"),
                    liste_salaire_offre = fiche.get("liste_salaire_offre")
                                )
                try:
                    session.add(fiche_insert)
                except Exception as e:
                    logger.exception(f"Erreur lors de l'ajout de la fiche {fiche.get('code')}: {e}")
                    continue

            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Erreur lors de la sauvegarde des métiers ROME : {str(e)}", exc_info=True)
        finally:
            session.close()

        return {"message": f"{len(fiche_metier)} métiers ROME chargées et sauvegardées avec succès"}

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