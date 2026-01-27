import xml.etree.ElementTree as ET
import pandas as pd
import requests
from tqdm.auto import tqdm
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from server.models import Offres_FT
import os
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


def get_access_token(CLIENT_ID, CLIENT_SECRET, AUTH_URL) -> str:
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


def search_offers(API_URL, NB_OFFRE, CLIENT_ID, CLIENT_SECRET, AUTH_URL) -> list[dict]:
    offers = []
    token = get_access_token(CLIENT_ID, CLIENT_SECRET, AUTH_URL)
    start_date = datetime(2020, 1, 1)

    # Start from the current date and paginate backwards
    max_creation_date = datetime.now()

    with tqdm(desc="Fetching job offers") as pbar:
        while max_creation_date >= start_date:
            page_start = 0
            has_more_results = True

            while has_more_results:
                # Respect API limits: page_start <= 3000, page_end <= 3149
                if page_start > 3000:
                    break

                page_end = min(page_start + 149, 3149)
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                }

                try:
                    params = {
                        "maxCreationDate": max_creation_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        "minCreationDate": start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        "range": f"{page_start}-{page_end}"

                    }
                    resp = requests.get(API_URL, headers=headers, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    print(f"Error: {e}")
                    print(f"Response: {resp.text if 'resp' in locals() else 'No response'}")
                    token = get_access_token(CLIENT_ID, CLIENT_SECRET, AUTH_URL)
                    headers = {
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                        "Range": f"{page_start}-{page_end}"
                    }
                    params = {
                        "maxCreationDate": max_creation_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        "minCreationDate": start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
                    }
                    resp = requests.get(API_URL, headers=headers, params=params)
                    resp.raise_for_status()
                    data = resp.json()

                results = data.get("resultats", [])
                if not results:
                    # No more results for this date range, move to previous date
                    has_more_results = False
                    break

                offers += results

                # Save results to database immediately
                save_offers_to_db(results)

                pbar.set_postfix({
                    "maxCreationDate": max_creation_date.strftime('%Y-%m-%d %H:%M:%S'),
                    "page": f"{page_start}-{page_end}",
                    "retrieved": len(results),
                    "total": len(offers)
                })
                pbar.update(1)

                # If we got fewer results than requested, we've reached the end of this date range
                if len(results) < 150:
                    has_more_results = False
                else:
                    page_start += 150

            # Use the last offer's creation date as the new maxCreationDate for the next request
            if offers:
                last_offer_date_str = offers[-1].get("dateCreation")
                if last_offer_date_str:
                    max_creation_date = datetime.fromisoformat(
                        last_offer_date_str.replace('Z', '+00:00')).replace(tzinfo=None)
                    # Subtract a small amount to ensure we don't skip offers with the same creation timestamp
                    max_creation_date -= timedelta(seconds=1)
                else:
                    break
            else:
                break

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
            try:
                session.add(offre)
                session.commit()
            except IntegrityError:
                session.rollback()
                # Skip duplicate entries
                continue

    except Exception as e:
        session.rollback()
        print(f"Erreur lors de la sauvegarde des offres : {e}")
    finally:
        session.close()


def get_offers(API_URL, NB_OFFRE, CLIENT_ID, CLIENT_SECRET, AUTH_URL):
    offres = search_offers(API_URL, NB_OFFRE, CLIENT_ID, CLIENT_SECRET, AUTH_URL)


if __name__ == "__main__":
    API_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"
    NB_OFFRE = 1000
    CLIENT_ID = "PAR_dux_dc80f0f45695a7c5d5baec8923f9fe0180cdfbf90d29c35307a8014e3275b200"
    CLIENT_SECRET = "20881cafb62205992dde84402208292faf4d976b01633d4f2d1e1e84adc5de48"
    AUTH_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token"

    get_offers(API_URL, NB_OFFRE, CLIENT_ID, CLIENT_SECRET, AUTH_URL)
