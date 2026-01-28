"""
Job search and France Travail API integration router.

Provides endpoints for searching job offers, loading offers from France Travail API,
and managing job-related data.
"""

import logging
import random
import requests
import re
import time

from fastapi import APIRouter, Query, Depends
from server.config import settings
from server.models import Metier_ROME, User, Offres_FT, Competence_ROME
from server.database import get_db_session
import json
from typing import Optional, Dict, Any, List, Union, Tuple

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from tqdm.auto import tqdm

from server.methods.FT_job_search import search_france_travail
from server.thread_pool import run_blocking_in_executor
from server.utils.dependencies import get_current_user
from server.methods.matching_engine import MatchingEngine
import asyncio

from sentence_transformers import SentenceTransformer
from pydantic import BaseModel
from fastapi import HTTPException


def _extract_url_from_text(text: str) -> Optional[str]:
    """
    Extract the first URL from text content.
    
    Searches for https:// or http:// URLs in the text and returns the first one found.
    
    Args:
        text: Text to search for URLs
        
    Returns:
        First URL found, or None if no URL is present
    """
    if not text:
        return None
    
    # Match URLs starting with http:// or https://
    url_pattern = r'https?://[^\s]+'
    match = re.search(url_pattern, text)
    
    if match:
        url = match.group(0)
        # Clean up trailing punctuation that might have been captured
        url = url.rstrip('.,;:)')
        return url
    
    return None


def get_token_api_FT(CLIENT_ID: str, CLIENT_SECRET: str, AUTH_URL: str, scope: str) -> str:
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": scope
    }
    params = {"realm": "/partenaire"}
    resp = requests.post(AUTH_URL, data=data, params=params, timeout=30)
    resp.raise_for_status()
    token = resp.json()["access_token"]

    return token


def get_offers(code_rome: str) -> dict:
    # Reuse centralized France Travail client with built-in retries/pagination
    return search_france_travail({"codeROME": code_rome}, nb_offres=300)


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
        "annuel": lambda: _parse_annuel(ts),
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

    # Extract application URL from contact info
    # Priority: explicit urlPostulation > URL in contact fields > URL in agence courriel > URL in origineOffre
    contact_url_postulation = contact.get("urlPostulation")
    if not contact_url_postulation:
        # Try extracting from contact fields (coordonnees3 often contains "Pour postuler, utiliser le lien suivant : URL")
        for field in ["coordonnees3", "coordonnees2", "coordonnees1"]:
            extracted = _extract_url_from_text(contact.get(field, ""))
            if extracted:
                contact_url_postulation = extracted
                break
    
    # If still not found, try agence courriel field
    if not contact_url_postulation:
        contact_url_postulation = _extract_url_from_text(agence.get("courriel", ""))
    
    # If still not found, use the origineOffre urlOrigine as fallback
    if not contact_url_postulation:
        contact_url_postulation = origine.get("urlOrigine")

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
        "contact_urlPostulation": contact_url_postulation,
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

def _get_with_retry(
    url: str,
    headers: Dict[str, str],
    timeout: int,
    max_retries: int = 5,
    base_delay: float = 1.0,
) -> requests.Response:
    for attempt in range(max_retries + 1):
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code != 429:
            return resp
        if attempt >= max_retries:
            logger.error("FT API rate limit exceeded after %s retries for %s", max_retries, url)
            resp.raise_for_status()
        delay = base_delay * (2 ** attempt) + random.uniform(0, base_delay)
        logger.warning(
            "FT API rate limit hit (attempt %s/%s). Retrying in %.2fs for %s",
            attempt + 1,
            max_retries,
            delay,
            url,
        )
        time.sleep(delay)

# ============================================================================
# Job Search Endpoints
# ============================================================================


@router.post("/load_offers", summary="Load offers from France Travail API")
async def load_offers(
    nb_offres: int = Query(150, description="Nombre d'offres à récupérer"),
    accesTravailleurHandicape: bool = Query(
        None, description="Offres ouvertes aux Bénéficiaires de l'Obligation d'Emploi"),
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
    employeursHandiEngages: bool = Query(
        None, description="Filtre les offres dont l'employeur est reconnu pour ses actions en faveur du handicap"),
    entreprisesAdaptees: bool = Query(
        None, description="Filtre les offres dont l'entreprise permet des conditions adaptées au handicap"),
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
def load_fiche_metier(
        codeROME: str = Query("A1413", description="Code ROME Offre à récupérer")
    ):

    """
    Charge des données depuis l'API France Travail en fonction des paramètres de recherche.
    """

    try:
        FT_CLIENT_ID = settings.ft_client_id
        FT_CLIENT_SECRET = settings.ft_client_secret
        FT_AUTH_URL = settings.ft_auth_url
        FT_API_URL_METIER = settings.ft_api_url_fiche_metier

        """
        Récupère un token OAuth2 en mode client_credentials.
        """

        token = get_token_api_FT(FT_CLIENT_ID, FT_CLIENT_SECRET, FT_AUTH_URL, "api_rome-metiersv1 nomenclatureRome")

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        
        champs = "?champs=accesemploi,appellations(code,classification,libelle),centresinteretslies(centreinteret(libelle,code,definition)),code,libelle,competencesmobiliseesprincipales(libelle,@macrosavoiretreprofessionnel(riasecmineur,riasecmajeur),@competencedetaillee(riasecmineur,riasecmajeur),code,@macrosavoirfaire(riasecmineur,riasecmajeur),codeogr),contextestravail(libelle,code,categorie),definition,domaineprofessionnel(libelle,code,granddomaine(libelle,code)),metiersenproximite(libelle,code),secteursactiviteslies(secteuractivite(libelle,code,secteuractivite(libelle,code,definition),definition)),themes(libelle,code),emploicadre,emploireglemente,transitiondemographique,transitionecologique,transitionnumerique"

        try:
            resp = _get_with_retry(
                FT_API_URL_METIER + f"/{codeROME}" + champs,
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            # Getting offers info from france travail API
            liste_offres = get_offers(codeROME)
            salaire = []
            for offre in liste_offres:
                salaire_obj = offre.get('salaire') or {}
                salaire.append(calcul_salaire(
                    salaire_obj.get('libelle'),
                    offre.get('dureeTravailLibelle')
                ))
        except (requests.RequestException, KeyError) as e:
            logger.warning("Initial fiche metier request failed, retrying with new token: %s", e)
            token = get_token_api_FT(FT_CLIENT_ID, FT_CLIENT_SECRET, FT_AUTH_URL, "api_rome-metiersv1 nomenclatureRome")
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            resp = _get_with_retry(
                FT_API_URL_METIER + f"/{codeROME}" + champs,
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

            # Getting offers info from france travail API
            liste_offres = get_offers(codeROME)
            salaire = []
            for offre in liste_offres:
                salaire_obj = offre.get('salaire') or {}
                salaire.append(calcul_salaire(
                    salaire_obj.get('libelle'),
                    offre.get('dureeTravailLibelle')
                ))

        if len(liste_offres) == 0:
            data['nb_offre'] = 0
            data['liste_salaire_offre'] = []
        else:
            data['nb_offre'] = len(liste_offres)
            data['liste_salaire_offre'] = salaire

        return data

    except Exception as e:
        return {"error": str(e)}


@router.post("/load_code_metier", summary="Load code metier from France Travail API (ROME)")
def load_code_metier():
    """
    Charge des données depuis l'API France Travail en fonction des paramètres de recherche.
    """

    try:
        FT_CLIENT_ID = settings.ft_client_id
        FT_CLIENT_SECRET = settings.ft_client_secret
        FT_AUTH_URL = settings.ft_auth_url
        FT_API_URL_CODE_METIER = settings.ft_api_url_code_metier
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
        except (requests.RequestException, KeyError) as e:
            logger.warning("Initial code metier request failed, retrying with new token: %s", e)
            token = get_token_api_FT(FT_CLIENT_ID, FT_CLIENT_SECRET, FT_AUTH_URL, "api_rome-metiersv1 nomenclatureRome")
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            resp = requests.get(FT_API_URL_CODE_METIER, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()


        code_metier += data


        logger.info(f"Enregistrement des codes métiers : {len(code_metier)} obtenues.")
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)

        if not code_metier:
            logger.warning("Aucun code métier reçu, rien à sauvegarder.")  
            return {"message": "Aucun code métier reçue"} 

        session = Session()
        session.execute(text("TRUNCATE TABLE Metier_ROME RESTART IDENTITY CASCADE;"))

        try:
            for fiche in code_metier:
                fiche_insert = Metier_ROME(
                    code = fiche.get("code"),
                    libelle = fiche.get("libelle"),
                                )
                try:
                    session.add(fiche_insert)
                except Exception as e:
                    logger.exception(f"Erreur lors de l'ajout du métier {fiche.get('code')}: {e}")
                    continue

            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Erreur lors de la sauvegarde des métiers ROME : {str(e)}", exc_info=True)
        finally:
            session.close()

        return {"message": f"{len(code_metier)} métiers ROME chargées et sauvegardées avec succès"}

    except Exception as e:
        return {"error": str(e)}
    

@router.post("/load_fiche_competence", summary="Load fiche competence from France Travail API (ROME)")
def load_fiche_competence(
        codeROME : str = Query("100253", description="Code ROME Compétence à récupérer")
    ):

    """
    Charge des données depuis l'API France Travail en fonction des paramètres de recherche.
    """

    try:
        FT_CLIENT_ID = settings.ft_client_id
        FT_CLIENT_SECRET = settings.ft_client_secret
        FT_AUTH_URL = settings.ft_auth_url
        FT_API_URL_COMPETENCE = settings.ft_api_url_fiche_competence

        """
        Récupère un token OAuth2 en mode client_credentials.
        """

        token = get_token_api_FT(FT_CLIENT_ID, FT_CLIENT_SECRET, FT_AUTH_URL, "api_rome-competencesv1 nomenclatureRome")

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        
        champs = ""
        
        try:
            resp = _get_with_retry(
                FT_API_URL_COMPETENCE + f"/{codeROME}" + champs,
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, KeyError) as e:
            logger.warning("Initial fiche metier request failed, retrying with new token: %s", e)
            token = get_token_api_FT(FT_CLIENT_ID, FT_CLIENT_SECRET, FT_AUTH_URL, "api_rome-competencesv1 nomenclatureRome")
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            resp = _get_with_retry(
                FT_API_URL_COMPETENCE + f"/{codeROME}" + champs,
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

        return data

    except Exception as e:
        return {"error": str(e)}


@router.post("/load_code_competences", summary="Load code competences from France Travail API (ROME)")
def load_code_competences():
    """
    Charge des données depuis l'API France Travail en fonction des paramètres de recherche.
    """

    try:
        FT_CLIENT_ID = settings.ft_client_id
        FT_CLIENT_SECRET = settings.ft_client_secret
        FT_AUTH_URL = settings.ft_auth_url
        FT_API_URL_CODE_COMPETENCE = settings.ft_api_url_code_competence
        DATABASE_URL = settings.database_url

        """
        Récupère un token OAuth2 en mode client_credentials.
        """

        token = get_token_api_FT(FT_CLIENT_ID, FT_CLIENT_SECRET, FT_AUTH_URL, "api_rome-competencesv1 nomenclatureRome")

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }

        # Récupérer les codes compétence ROME
        code_competence = []

        # Getting the list of ROME codes
        try:
            resp = requests.get(FT_API_URL_CODE_COMPETENCE, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, KeyError) as e:
            logger.warning("Initial code metier request failed, retrying with new token: %s", e)
            token = get_token_api_FT(FT_CLIENT_ID, FT_CLIENT_SECRET, FT_AUTH_URL, "api_rome-metiersv1 nomenclatureRome")
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            resp = requests.get(FT_API_URL_CODE_COMPETENCE, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()

        code_competence += data


        logger.info(f"Enregistrement des codes compétences : {len(code_competence)} obtenues.")
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)

        if not code_competence:
            logger.warning("Aucun code competence reçu, rien à sauvegarder.")  
            return {"message": "Aucun code competence reçue"} 

        session = Session()
        session.execute(text("TRUNCATE TABLE Competence_ROME RESTART IDENTITY CASCADE;"))

        try:
            for fiche in code_competence:
                fiche_insert = Competence_ROME(
                    code = fiche.get("code"),
                    libelle = fiche.get("libelle"),
                                )
                try:
                    session.add(fiche_insert)
                except Exception as e:
                    logger.exception(f"Erreur lors de l'ajout du métier {fiche.get('code')}: {e}")
                    continue

            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Erreur lors de la sauvegarde des compétences ROME : {str(e)}", exc_info=True)
        finally:
            session.close()

        return {"message": f"{len(code_competence)} compétences ROME chargées et sauvegardées avec succès"}

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
    lang: str = "fr"  # <--- Ajout du paramètre
):
    SessionLocal = sessionmaker(bind=bind)
    with SessionLocal() as session:
        user = session.get(User, user_id)
        if not user:
            raise ValueError("Utilisateur introuvable dans le thread")

        if job_payload is None:
            job = session.query(Offres_FT).filter(Offres_FT.id == job_id).first()
            if not job:
                raise ValueError("Offre introuvable dans le thread")
        else:
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

        engine = MatchingEngine(session)
        return engine.analyser_match(user, job, lang)


@router.get("/analyze/{job_id}")
async def analyze_specific_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    bind = db.get_bind()
    user_id = current_user.id
    logger.info(f"Analyse demandée par : {current_user.username} pour l'offre {job_id}")

    try:
        evaluation = await asyncio.to_thread(
            _run_analysis_in_thread,
            user_id,
            job_id,
            None,
            bind,
            "fr"
        )

        offre = db.query(Offres_FT).filter(Offres_FT.id == job_id).first()
        return {
            "status": "success",
            "candidat": {"nom": f"{current_user.first_name} {current_user.last_name}"},
            "job": {"id": job_id, "intitule": offre.intitule if offre else "N/A"},
            "analysis": evaluation
        }
    except Exception as e:
        logger.error(f"Erreur critique analyse : {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class JobDataForAnalysis(BaseModel):
    id: str
    intitule: Optional[str] = None
    description: Optional[str] = None
    entreprise_nom: Optional[str] = None
    competences: Optional[Any] = None
    lang: str = "fr"


@router.post("/analyze")
async def analyze_job_direct(
    job_data: JobDataForAnalysis,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    bind = db.get_bind()
    user_id = current_user.id
    lang = job_data.lang  # <--- On récupère la langue

    logger.info(f"Analyse directe ({lang}) demandée par : {current_user.username}")

    try:
        payload = job_data.model_dump()

        evaluation = await asyncio.to_thread(
            _run_analysis_in_thread,
            user_id,
            None,
            payload,
            bind,
            lang  # <--- On la passe au thread
        )

        return {
            "status": "success",
            "candidat": {"nom": f"{current_user.first_name} {current_user.last_name}"},
            "job": {"id": job_data.id},
            "analysis": evaluation
        }
    except Exception as e:
        logger.error(f"Erreur critique analyse directe : {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/offer/{job_id}", summary="Get job offer details by ID")
async def get_job_offer(
    job_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Fetch full job offer details from France Travail API by ID.
    Used by frontend to display full job details when showing optimal offers.
    """
    try:
        from server.methods.FT_job_search import get_offer_by_id

        offer_data = await asyncio.to_thread(get_offer_by_id, job_id)

        # Flatten the offer structure to match frontend expectations
        flattened_offer = _flatten_offer(offer_data)

        return {
            "status": "success",
            "offer": flattened_offer
        }

    except ValueError as e:
        error_msg = str(e).lower()

        # Check if it's a "not found" error (404)
        if "not found" in error_msg:
            logger.warning(f"Job offer not found: job_id={job_id}, error={str(e)}")
            raise HTTPException(status_code=404, detail=f"Job offer {job_id} not found")

        # Check if it's a "bad request" error (400)
        elif "bad request" in error_msg:
            logger.warning(f"Bad request for job offer: job_id={job_id}, error={str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

        # Other ValueError cases - log and return 500
        else:
            logger.error(f"Error fetching job offer: job_id={job_id}, error={str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching job offer: job_id={job_id}, error={str(e)}, type={type(e).__name__}")
        raise HTTPException(status_code=500, detail=str(e))
