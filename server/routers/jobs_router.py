import logging
import time
import token
import requests
import re

from fastapi import APIRouter, Query, Depends
from server.config import settings
from server.models import Metier_ROME
from server.database import get_db_session
from server.methods.job_search import search_job_offers
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from tqdm.auto import tqdm

def get_token_api_FT(CLIENT_ID: str, CLIENT_SECRET: str, AUTH_URL: str, scope: str) -> str:
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": scope,
    }
    params = {"realm": "/partenaire"}

    resp = requests.post(AUTH_URL, data=data, params=params)
    resp.raise_for_status()
    token = resp.json()["access_token"]

    return token

def get_offers(code_rome: str) -> dict:
    FT_CLIENT_ID = settings.ft_client_id
    FT_CLIENT_SECRET = settings.ft_client_secret
    FT_AUTH_URL = settings.ft_auth_url
    FT_API_OFFRES_URL = settings.ft_api_url_offres

    """
    Récupère un token OAuth2 en mode client_credentials.
    """

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
            resp = requests.get(FT_API_OFFRES_URL + f"?codeROME={code_rome}&range={page * 150}-{page * 150 + 149}", headers=headers)
            resp.raise_for_status()
        except:
            token = get_token_api_FT(FT_CLIENT_ID, FT_CLIENT_SECRET, FT_AUTH_URL, "api_offresdemploiv2 o2dsoffre")

            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            resp = requests.get(FT_API_OFFRES_URL + f"?codeROME={code_rome}&range={page * 150}-{page * 150 + 149}", headers=headers)
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

def calcul_salaire(texte_salaire: str, texte_heure: str) -> float:
    if texte_salaire == None:
        return None
    elif texte_salaire[0:7] == "Mensuel":
        try:
            try:
                pattern = r"Mensuel\s+de\s+([\d.,]+)\s*Euros\s+sur\s+([\d.,]+)\s*mois"
                m = re.search(pattern, texte_salaire, flags=re.IGNORECASE)

                if not m:
                    raise ValueError("Format non reconnu")

                salaire_mensuel = float(m.group(1).replace(",", "."))
                nb_mois = float(m.group(2).replace(",", "."))
            except:
                pattern = r"Mensuel\s+de\s+([\d.,]+)\s*Euros"
                m = re.search(pattern, texte_salaire, flags=re.IGNORECASE)

                if not m:
                    raise ValueError("Format non reconnu")

                salaire_mensuel = float(m.group(1).replace(",", "."))
                nb_mois = 12.0
        except:
            try:
                pattern = r"Mensuel\s+de\s+([\d.,]+)\s*Euros\s+à\s+([\d.,]+)\s*Euros\s+sur\s+([\d.,]+)\s*mois"
                m = re.search(pattern, texte_salaire, flags=re.IGNORECASE)

                if not m:
                    raise ValueError("Format non reconnu")

                salaire_mensuel_inf = float(m.group(1).replace(",", "."))
                salaire_mensuel_sup = float(m.group(2).replace(",", "."))
                nb_mois = float(m.group(3).replace(",", "."))

                salaire_mensuel = (salaire_mensuel_inf + salaire_mensuel_sup) / 2.0
            except:
                pattern = r"Mensuel\s+de\s+([\d.,]+)\s*Euros\s+à\s+([\d.,]+)\s*Euros"
                m = re.search(pattern, texte_salaire, flags=re.IGNORECASE)

                if not m:
                    raise ValueError("Format non reconnu")

                salaire_mensuel_inf = float(m.group(1).replace(",", "."))
                salaire_mensuel_sup = float(m.group(2).replace(",", "."))
                nb_mois = 12.0

                salaire_mensuel = (salaire_mensuel_inf + salaire_mensuel_sup) / 2.0

        annuel = salaire_mensuel * nb_mois
        salaire = annuel / 12
    elif texte_salaire[0:7] == "Horaire":
        try:
            pattern = r"Horaire\s+de\s+([\d.,]+)\s*Euros\s+sur\s+([\d.,]+)\s*mois"
            m = re.search(pattern, texte_salaire, flags=re.IGNORECASE)
            if not m:
                raise ValueError("Format non reconnu")
            
            salaire_horaire = float(m.group(1).replace(",", "."))
            nb_mois = float(m.group(2).replace(",", "."))

        except:
            try:
                pattern = r"Horaire\s+de\s+([\d.,]+)\s*Euros\s+à\s+([\d.,]+)\s*Euros\s+sur\s+([\d.,]+)\s*mois"
                m = re.search(pattern, texte_salaire, flags=re.IGNORECASE)
                if not m:
                    raise ValueError("Format non reconnu")
                
                salaire_horaire_inf = float(m.group(1).replace(",", "."))
                salaire_horaire_sup = float(m.group(2).replace(",", "."))
                nb_mois = float(m.group(3).replace(",", "."))
                salaire_horaire = (salaire_horaire_inf + salaire_horaire_sup) / 2.0

            except:
                try:
                    pattern = r"Horaire\s+de\s+([\d.,]+)\s*Euros\s+à\s+([\d.,]+)\s*Euros"
                    m = re.search(pattern, texte_salaire, flags=re.IGNORECASE)
                    if not m:
                        raise ValueError("Format non reconnu")
                    
                    salaire_horaire_inf = float(m.group(1).replace(",", "."))
                    salaire_horaire_sup = float(m.group(2).replace(",", "."))
                    nb_mois = 12.0
                    salaire_horaire = (salaire_horaire_inf + salaire_horaire_sup) / 2.0
                except:
                    pattern = r"Horaire\s+de\s+([\d.,]+)\s*Euros"
                    m = re.search(pattern, texte_salaire, flags=re.IGNORECASE)
                    if not m:
                        raise ValueError("Format non reconnu")
                    
                    salaire_horaire = float(m.group(1).replace(",", "."))
                    nb_mois = 12.0
                    
        
        texte_heure = re.sub(r"(semaine)\b.*$", r"\1", texte_heure, flags=re.S)
        try:
            try:
                pattern_horaire = r"Temps\s+partiel\s+-\s+([\d.,]+)H/semaine\b.*$"
                horaire = re.search(pattern_horaire,texte_heure, flags=re.IGNORECASE)
                if not horaire:
                    raise ValueError("Format horaire non reconnu")
                
                nb_heures_semaine = float(horaire.group(1).replace(",", "."))

            except:
                try:
                    pattern_horaire = r"([\d.,]+)H/semaine.*$"
                    horaire = re.search(pattern_horaire,texte_heure, flags=re.IGNORECASE)
                    if not horaire:
                        raise ValueError("Format horaire non reconnu")
                    
                    nb_heures_semaine = float(horaire.group(1).replace(",", "."))

                except:
                    pattern_horaire = r"([\d.,]+)H([\d.,]+)/semaine.*$"
                    horaire = re.search(pattern_horaire,texte_heure, flags=re.IGNORECASE)
                    if not horaire:
                        raise ValueError("Format horaire non reconnu")
                    
                    nb_heures_semaine = float(horaire.group(1).replace(",", "."))
                    nb_heures_semaine += float(horaire.group(2).replace(",", "."))/60.0
        except:
            nb_heures_semaine = 35.0

        annuel = salaire_horaire * nb_heures_semaine * 52.0 * (nb_mois / 12.0)
        salaire = annuel / 12

    elif texte_salaire[0:6] == "Annuel":
        try:
            pattern = r"Annuel\s+de\s+([\d.,]+)\s*Euros\s+sur\s+([\d.,]+)\s*mois"
            m = re.search(pattern, texte_salaire, flags=re.IGNORECASE)

            if not m:
                raise ValueError("Format non reconnu")
            
            salaire_annuel = float(m.group(1).replace(",", "."))
            nb_mois = float(m.group(2).replace(",", "."))
        except:
            try:
                pattern = r"Annuel\s+de\s+([\d.,]+)\s*Euros\s+à\s+([\d.,]+)\s*Euros\s+sur\s+([\d.,]+)\s*mois"
                m = re.search(pattern, texte_salaire, flags=re.IGNORECASE)

                if not m:
                    raise ValueError("Format non reconnu")

                salaire_annuel_inf = float(m.group(1).replace(",", "."))
                salaire_annuel_sup = float(m.group(2).replace(",", "."))
                nb_mois = float(m.group(3).replace(",", "."))

                salaire_annuel = (salaire_annuel_inf + salaire_annuel_sup) / 2.0
            except:
                try:
                    pattern = r"Annuel\s+de\s+([\d.,]+)\s*Euros"
                    m = re.search(pattern, texte_salaire, flags=re.IGNORECASE)

                    if not m:
                        raise ValueError("Format non reconnu")
                    
                    salaire_annuel = float(m.group(1).replace(",", "."))
                    nb_mois = 12.0
                except:
                    salaire_annuel = None

        if salaire_annuel == None:
            salaire = None
        else:
            annuel = salaire_annuel * (nb_mois/12.0)
            salaire = annuel / 12
    else:
        salaire = None

    return salaire

router = APIRouter(prefix="/jobs", tags=["Jobs"])
logger = logging.getLogger(__name__)


@router.get("/search", summary="Search job offers")
def search_jobs(
    q: str = Query(None, description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    db: Session = Depends(get_db_session)
):
    """
    Search job offers from the database with text search and pagination.

    - **q**: Search query (searches in job title, description, location, company name, etc.)
    - **page**: Page number for pagination (default: 1)
    - **page_size**: Number of results per page (default: 20, max: 100)
    """
    try:
        result = search_job_offers(db, query=q, page=page, page_size=page_size)
        return result
    except Exception as e:
        logger.error(f"Error searching jobs: {e}")
        return {"error": str(e), "results": [], "page": page, "page_size": page_size, "total": 0}


@router.post("/load_offers", summary="Load offers from France Travail API")
def load_offers(
    nb_offres: int = Query(2, description="Nombre d'offres à récupérer"),
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
        FT_CLIENT_ID = settings.ft_client_id
        FT_CLIENT_SECRET = settings.ft_client_secret
        FT_AUTH_URL = settings.ft_auth_url
        FT_API_URL = settings.ft_api_url_offres

        # Get OAuth2 token
        auth_data = {
            "grant_type": "client_credentials",
            "client_id": FT_CLIENT_ID,
            "client_secret": FT_CLIENT_SECRET,
            "scope": f"api_offresdemploiv2 o2dsoffre application_{FT_CLIENT_ID}",
        }
        auth_params = {"realm": "/partenaire"}

        resp = requests.post(FT_AUTH_URL, data=auth_data, params=auth_params)
        resp.raise_for_status()
        token = resp.json()["access_token"]

        # Retrieve offers from API
        offers = []

        for i in range(0, nb_offres, 150):
            headers = build_headers(token)
            headers["range"] = f"{i}-{nb_offres if i+150 > nb_offres else i+150}"

            try:
                resp = requests.get(FT_API_URL, headers=headers)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                logger.warning(f"Request failed: {e}, refreshing token...")
                # Refresh token on error
                resp = requests.post(FT_AUTH_URL, data=auth_data, params=auth_params)
                resp.raise_for_status()
                token = resp.json()["access_token"]

                headers = build_headers(token)
                headers["range"] = f"{i}-{nb_offres if i+150 > nb_offres else i+150}"
                resp = requests.get(FT_API_URL, headers=headers)
                resp.raise_for_status()
                data = resp.json()

            offers.append(data.get("resultats", []))
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
            resp = requests.get(FT_API_URL_CODE_METIER, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        except:
            token = get_token_api_FT(FT_CLIENT_ID, FT_CLIENT_SECRET, FT_AUTH_URL, "api_rome-metiersv1 nomenclatureRome")
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            resp = requests.get(FT_API_URL_CODE_METIER, headers=headers)
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
                    resp = requests.get(FT_API_URL_METIER + f"/{code.get("code")}" + champs, headers=headers)
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
                    resp = requests.get(FT_API_URL_METIER + f"/{code.get("code")}" + champs, headers=headers)
                    if resp.status_code != 429:
                        break
                
                resp.raise_for_status()
                data = resp.json()

                # Getting offers info from france travail API
                liste_offres = get_offers(code.get("code"))
                salaire = []
                for offre in liste_offres:
                    print(str(offre.get("salaire").get('libelle')), str(offre.get('dureeTravailLibelle')))
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
        
        # Sauvegarde du résultat dans une base de données
        # Create a session factory
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
                except:
                    logger.info(f"Le métier ROME {fiche.get('code')} existe déjà en base de données.")

            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Erreur lors de la sauvegarde des métiers ROME : {str(e)}", exc_info=True)
        finally:
            session.close()

        return {"message": f"{len(fiche_metier)} métiers ROME chargées et sauvegardées avec succès"}

    except Exception as e:
        return {"error": str(e)}
