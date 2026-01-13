import logging

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request, Query
from fastapi.encoders import jsonable_encoder
from server.methods.upload import upload_file
from server.methods.job_search import search_job_offers
from server.database import get_db_session
from server.models import User, Experience, Education, Fiche_Metier_ROME    
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine, inspect, text
from pydantic import BaseModel
from typing import List, Optional
from server.config import settings
import requests
import pandas as pd
import os
import logging
import json

router = APIRouter(tags=["General"])
logger = logging.getLogger(__name__)


class ExperienceData(BaseModel):
    company: str
    title: str
    startDate: str
    endDate: Optional[str] = None
    isCurrent: bool = False
    description: Optional[str] = None


class EducationData(BaseModel):
    school: str
    degree: str
    fieldOfStudy: Optional[str] = None
    startDate: str
    endDate: Optional[str] = None
    description: Optional[str] = None


class ProfileSetupRequest(BaseModel):
    headline: Optional[str] = None
    summary: Optional[str] = None
    location: Optional[str] = None
    skills: List[str] = []
    experiences: List[ExperienceData] = []
    educations: List[EducationData] = []


def get_current_user(request: Request, db: Session = Depends(get_db_session)) -> User:
    """
    Dependency to get the current authenticated user.

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        User: The authenticated user object

    Raises:
        HTTPException: If user is not authenticated or not found
    """
    if "username" not in request.session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = db.query(User).filter(User.username == request.session["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.get("/healthcheck", summary="Health check")
def read_root() -> str:
    """
    Healthcheck endpoint to verify that the application is running.

    Returns:
        str: "OK" if the service is running
    """
    return "OK"


@router.post("/upload", summary="Upload file")
async def upload_endpoint(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Upload endpoint to handle file uploads (CV).

    Args:
        request: FastAPI request object
        file: The file to upload (multipart/form-data)
        db: Database session
        current_user: Current authenticated user

    Returns:
        dict: Upload result containing filename, content_type, size, and message
    """
    result = await upload_file(file)

    # Update user's CV filename in database
    current_user.cv_filename = result["filename"]
    db.commit()

    return result


@router.post("/profile/setup", summary="Complete profile setup")
async def complete_profile_setup(
    request: Request,
    data: ProfileSetupRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Complete user profile setup after registration.

    Args:
        data: Profile setup data including headline, summary, skills, experience, education
        db: Database session
        current_user: Current authenticated user

    Returns:
        dict: Success message
    """
    try:
        # Update user profile fields
        if data.headline:
            current_user.headline = data.headline
        if data.summary:
            current_user.summary = data.summary
        if data.location:
            current_user.location = data.location
        if data.skills:
            current_user.skills = data.skills

        # Delete existing experiences and educations for this user
        db.query(Experience).filter(Experience.user_id == current_user.id).delete()
        db.query(Education).filter(Education.user_id == current_user.id).delete()

        # Add new experiences
        for exp_data in data.experiences:
            experience = Experience(
                user_id=current_user.id,
                company=exp_data.company,
                title=exp_data.title,
                start_date=exp_data.startDate,
                end_date=exp_data.endDate if not exp_data.isCurrent else None,
                is_current=exp_data.isCurrent,
                description=exp_data.description
            )
            db.add(experience)

        # Add new educations
        for edu_data in data.educations:
            education = Education(
                user_id=current_user.id,
                school=edu_data.school,
                degree=edu_data.degree,
                field_of_study=edu_data.fieldOfStudy,
                start_date=edu_data.startDate,
                end_date=edu_data.endDate,
                description=edu_data.description
            )
            db.add(education)

        # Mark profile setup as completed
        current_user.profile_setup_completed = True

        db.commit()

        return {"message": "Profile setup completed successfully"}

    except Exception as e:
        db.rollback()
        # Log error for debugging
        import logging
        logging.error(f"Profile setup failed for user {current_user.id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to complete profile setup")


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
    try:
                
        CLIENT_ID = settings.client_id
        CLIENT_SECRET = settings.client_secret
        AUTH_URL = settings.auth_url
        API_URL_OFFRES = settings.api_url_offres

        """
        Récupère un token OAuth2 en mode client_credentials.
        """
        data = {
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scope": f"api_offresdemploiv2 o2dsoffre application_{CLIENT_ID}",
        }
        params = {"realm": "/partenaire"}

        resp = requests.post(AUTH_URL, data=data, params=params)
        resp.raise_for_status()
        token = resp.json()["access_token"]


        # Récupérer les offres depuis l'API
        offers = []

        for i in range(0,nb_offres,150):
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "range": f"{i}-{nb_offres if i+150 > nb_offres else i+150}",
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
                resp = requests.get(API_URL_OFFRES, headers=headers)
                resp.raise_for_status()
                data = resp.json()
            except:
                data = {
                    "grant_type": "client_credentials",
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "scope": f"api_offresdemploiv2 o2dsoffre application_{CLIENT_ID}",
                }
                params = {"realm": "/partenaire"}

                resp = requests.post(AUTH_URL, data=data, params=params)
                resp.raise_for_status()
                token = resp.json()["access_token"]
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "range": f"{i}-{nb_offres if i+150 > nb_offres else i+150}",
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
                resp = requests.get(API_URL_OFFRES, headers=headers)
                resp.raise_for_status()
                data = resp.json()

            offers += data.get("resultats", [])
            logger = logging.getLogger("uvicorn.info")
            logger.info(f"Récupération des offres : {len(offers)}/{nb_offres} obtenues.")
            
        # Renvoi du résultat
        return offers
    
    except Exception as e:
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
    
