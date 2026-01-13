import logging
import requests

from fastapi import APIRouter, Query
from server.config import settings
from server.models import Fiche_Metier_ROME
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

router = APIRouter(prefix="/jobs", tags=["Jobs"])
logger = logging.getLogger(__name__)


@router.post("/load_offers", summary="Load offers from France Travail API")
def load_offers(
    nb_offres: int = Query(10, description="Nombre d'offres à récupérer"),
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
    def build_headers(token: str) -> dict:
        """Build headers dictionary for API request"""
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
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

    try:
        CLIENT_ID = settings.client_id
        CLIENT_SECRET = settings.client_secret
        AUTH_URL = settings.auth_url
        API_URL = settings.api_url_offres

        # Get OAuth2 token
        auth_data = {
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scope": f"api_offresdemploiv2 o2dsoffre application_{CLIENT_ID}",
        }
        auth_params = {"realm": "/partenaire"}

        resp = requests.post(AUTH_URL, data=auth_data, params=auth_params)
        resp.raise_for_status()
        token = resp.json()["access_token"]

        # Retrieve offers from API
        offers = []

        for i in range(0, nb_offres, 150):
            headers = build_headers(token)
            headers["range"] = f"{i}-{nb_offres if i+150 > nb_offres else i+150}"

            try:
                resp = requests.get(API_URL, headers=headers)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                logger.warning(f"Request failed: {e}, refreshing token...")
                # Refresh token on error
                resp = requests.post(AUTH_URL, data=auth_data, params=auth_params)
                resp.raise_for_status()
                token = resp.json()["access_token"]

                headers = build_headers(token)
                headers["range"] = f"{i}-{nb_offres if i+150 > nb_offres else i+150}"
                resp = requests.get(API_URL, headers=headers)
                resp.raise_for_status()
                data = resp.json()

            offers += data.get("resultats", [])
            logger.info(f"Récupération des offres : {len(offers)}/{nb_offres} obtenues.")

        return offers

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
            resp = requests.get(API_URL_FICHE_METIER, headers=headers)
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

        # Sauvegarde du résultat dans une base de données
        # Create a session factory
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
                    code = fiche.get("code"),
                    metier = fiche.get("metier"),  # {code, libelle}
                    groupesCompetencesMobilisees = fiche.get("groupesCompetencesMobilisees"),  # Array of competency groups
                    groupesSavoirs = fiche.get("groupesSavoirs")  # Array of knowledge groups
                )
                try:
                    session.add(fiche_insert)
                except:
                    logger.info(f"La fiche métier ROME {fiche.get('code')} existe déjà en base de données.")

            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Erreur lors de la sauvegarde des fiches métiers ROME : {str(e)}", exc_info=True)
        finally:
            session.close()

        return {"message": f"{len(fiche_metier)} fiches métiers ROME chargées et sauvegardées avec succès"}

    except Exception as e:
        return {"error": str(e)}    
