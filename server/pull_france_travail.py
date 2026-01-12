import xml.etree.ElementTree as ET
import pandas as pd
import requests
from tqdm.auto import tqdm
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from models import Offres_FT
import os
from dotenv import load_dotenv
import json

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def get_access_token(CLIENT_ID,CLIENT_SECRET,AUTH_URL) -> str:
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
    return token


def search_offers(API_URL,NB_OFFRE,CLIENT_ID,CLIENT_SECRET,AUTH_URL) -> list[dict]:
    offers = []
    token = get_access_token(CLIENT_ID,CLIENT_SECRET,AUTH_URL)

    for i in tqdm(range(0,NB_OFFRE,150)):
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "range": f"{i}-{NB_OFFRE if i+150 > NB_OFFRE else i+150}"
        }

        try:
            resp = requests.get(API_URL, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        except:
            token = get_access_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "range": f"{i}-{NB_OFFRE if i+150 > NB_OFFRE else i+150}"
            }
            resp = requests.get(API_URL, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        offers += data.get("resultats", [])
    return offers


# Create a session factory
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def save_offers_to_db(offers: list[dict]) -> None:
    if not offers:
        print("Aucune offre reçue, rien à sauvegarder.")
        return

    session = Session()
    try:
        for offer in offers:
            offre = Offres_FT(
                id=offer.get("id"),
                intitule=offer.get("intitule"),
                description=offer.get("description"),
                dateCreation=offer.get("dateCreation"),
                dateActualisation=offer.get("dateActualisation"),
                romeCode=offer.get("romeCode"),
                romeLibelle=offer.get("romeLibelle"),
                appellationlibelle=offer.get("appellationlibelle"),
                typeContrat=offer.get("typeContrat"),
                typeContratLibelle=offer.get("typeContratLibelle"),
                natureContrat=offer.get("natureContrat"),
                experienceExige=offer.get("experienceExige"),
                experienceLibelle=offer.get("experienceLibelle"),
                competences=json.dumps(offer.get("competences")),
                dureeTravailLibelle=offer.get("dureeTravailLibelle"),
                dureeTravailLibelleConverti=offer.get("dureeTravailLibelleConverti"),
                alternance=offer.get("alternance"),
                nombrePostes=offer.get("nombrePostes"),
                accessibleTH=offer.get("accessibleTH"),
                qualificationCode=offer.get("qualificationCode"),
                qualificationLibelle=offer.get("qualificationLibelle"),
                codeNAF=offer.get("codeNAF"),
                secteurActivite=offer.get("secteurActivite"),
                secteurActiviteLibelle=offer.get("secteurActiviteLibelle"),
                offresManqueCandidats=offer.get("offresManqueCandidats"),
                entrepriseAdaptee=offer.get("entrepriseAdaptee"),
                employeurHandiEngage=offer.get("employeurHandiEngage"),
                lieuTravail_libelle=offer.get("lieuTravail", {}).get("libelle"),
                lieuTravail_latitude=offer.get("lieuTravail", {}).get("latitude"),
                lieuTravail_longitude=offer.get("lieuTravail", {}).get("longitude"),
                lieuTravail_codePostal=offer.get("lieuTravail", {}).get("codePostal"),
                lieuTravail_commune=offer.get("lieuTravail", {}).get("commune"),
                entreprise_nom=offer.get("entreprise", {}).get("nom"),
                entreprise_entrepriseAdaptee=offer.get("entreprise", {}).get("entrepriseAdaptee"),
                salaire_libelle=offer.get("salaire", {}).get("libelle"),
                salaire_complement1=offer.get("salaire", {}).get("complement1"),
                salaire_listeComplements=json.dumps(offer.get("salaire", {}).get("listeComplements")),
                contact_nom=offer.get("contact", {}).get("nom"),
                contact_coordonnees1=offer.get("contact", {}).get("coordonnees1"),
                contact_coordonnees2=offer.get("contact", {}).get("coordonnees2"),
                contact_coordonnees3=offer.get("contact", {}).get("coordonnees3"),
                contact_courriel=offer.get("contact", {}).get("courriel"),
                contact_urlPostulation=offer.get("contact", {}).get("urlPostulation"),
                contact_telephone=offer.get("contact", {}).get("telephone"),
                origineOffre_origine=offer.get("origineOffre", {}).get("origine"),
                origineOffre_urlOrigine=offer.get("origineOffre", {}).get("urlOrigine"),
                contexteTravail_horaires=json.dumps(offer.get("contexteTravail", {}).get("horaires")),
                contexteTravail_conditionsExercice=offer.get("contexteTravail", {}).get("conditionsExercice"),
                formations=json.dumps(offer.get("formations")),
                qualitesProfessionnelles=json.dumps(offer.get("qualitesProfessionnelles")),
                langues=json.dumps(offer.get("langues")),
                permis=json.dumps(offer.get("permis")),
                entreprise_logo=offer.get("entreprise", {}).get("logo"),
                entreprise_description=offer.get("entreprise", {}).get("description"),
                entreprise_url=offer.get("entreprise", {}).get("url"),
                agence_courriel=offer.get("agence", {}).get("courriel"),
                salaire_commentaire=offer.get("salaire", {}).get("commentaire"),
                deplacementCode=offer.get("deplacementCode"),
                deplacementLibelle=offer.get("deplacementLibelle"),
                trancheEffectifEtab=offer.get("trancheEffectifEtab"),
                experienceCommentaire=offer.get("experienceCommentaire"),
            )
            session.add(offre)

        session.commit()
        print(f"{len(offers)} offres sauvegardées dans la base de données.")
    except Exception as e:
        session.rollback()
        print(f"Erreur lors de la sauvegarde des offres : {e}")
    finally:
        session.close()

def get_offers(API_URL, NB_OFFRE, CLIENT_ID, CLIENT_SECRET, AUTH_URL):
    offres = search_offers(API_URL, NB_OFFRE, CLIENT_ID, CLIENT_SECRET, AUTH_URL)
    save_offers_to_db(offres)

if __name__ == "__main__":
    API_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"
    NB_OFFRE = 1000
    CLIENT_ID = "PAR_dux_dc80f0f45695a7c5d5baec8923f9fe0180cdfbf90d29c35307a8014e3275b200"
    CLIENT_SECRET = "20881cafb62205992dde84402208292faf4d976b01633d4f2d1e1e84adc5de48"
    AUTH_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token"

    get_offers(API_URL, NB_OFFRE, CLIENT_ID, CLIENT_SECRET, AUTH_URL)