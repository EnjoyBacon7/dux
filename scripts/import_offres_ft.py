import sys
import os
import requests
import json
from tqdm.auto import tqdm
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 1. AJOUT DU DOSSIER PARENT AU PATH (Pour trouver server.models)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.models import Offres_FT  # Import correct
from server.database import DATABASE_URL # On réutilise l'URL du projet

load_dotenv()

# Si DATABASE_URL n'est pas chargée via l'import server.database
if not DATABASE_URL:
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
    
    # On commence à chercher à partir de 2024 pour le test (plus rapide)
    # Tu peux remettre 2020 si tu veux tout l'historique
    start_date = datetime(2024, 1, 1) 
    max_creation_date = datetime.now()
    
    # Création du moteur DB pour la sauvegarde
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    
    with tqdm(desc="Fetching job offers") as pbar:
        while max_creation_date >= start_date:
            page_start = 0
            has_more_results = True
            
            while has_more_results:
                if page_start > 3000: # Limite API France Travail
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
                    
                    if resp.status_code == 206: # Partial content
                        data = resp.json()
                    elif resp.status_code == 200:
                        data = resp.json()
                    else:
                        print(f"Status {resp.status_code}: {resp.text}")
                        break

                except Exception as e:
                    print(f"Error, refreshing token: {e}")
                    token = get_access_token(CLIENT_ID, CLIENT_SECRET, AUTH_URL)
                    continue
                
                results = data.get("resultats", [])
                if not results:
                    has_more_results = False
                    break
                
                # Sauvegarde immédiate dans la DB
                save_offers_to_db(Session, results)
                offers += results
                
                pbar.set_postfix({
                    "date": max_creation_date.strftime('%Y-%m-%d'),
                    "retrieved": len(results)
                })
                pbar.update(len(results))
                
                if len(results) < 150:
                    has_more_results = False
                else:
                    page_start += 150
            
            # Gestion de la pagination temporelle
            if offers:
                last_offer_date_str = results[-1].get("dateCreation") if results else None
                if last_offer_date_str:
                    try:
                        # Nettoyage du format de date
                        last_date = datetime.fromisoformat(last_offer_date_str.replace('Z', '+00:00'))
                        max_creation_date = last_date.replace(tzinfo=None) - timedelta(seconds=1)
                    except ValueError:
                         max_creation_date -= timedelta(hours=1)
                else:
                    break
            else:
                break
    
    return offers

def clean_list_for_db(item_list):
    """
    Transforme une liste de dictionnaires en liste de chaînes de caractères
    pour compatibilité avec ARRAY(Text) de Postgres.
    Exemple: [{'libelle': 'Java'}] -> ['Java']
    """
    if not item_list:
        return None
    
    result = []
    for item in item_list:
        if isinstance(item, dict):
            # On essaie de récupérer le libellé s'il existe
            val = item.get('libelle') or item.get('code') or str(item)
            result.append(val)
        elif isinstance(item, str):
            result.append(item)
    return result

def save_offers_to_db(Session, offers: list[dict]) -> None:
    session = Session()
    try:
        for offer in offers:
            # Conversion des dates
            try:
                date_c = datetime.fromisoformat(offer.get("dateCreation").replace('Z', '+00:00')) if offer.get("dateCreation") else None
                date_a = datetime.fromisoformat(offer.get("dateActualisation").replace('Z', '+00:00')) if offer.get("dateActualisation") else None
            except:
                date_c, date_a = None, None

            # Préparation des listes pour les champs ARRAY
            # IMPORTANT : Postgres ARRAY attend une liste Python [], pas un json.dumps() string
            competences_list = clean_list_for_db(offer.get("competences"))
            formations_list = clean_list_for_db(offer.get("formations"))
            langues_list = clean_list_for_db(offer.get("langues"))
            permis_list = clean_list_for_db(offer.get("permis"))
            qualites_list = clean_list_for_db(offer.get("qualitesProfessionnelles"))
            salaire_comps_list = clean_list_for_db(offer.get("salaire", {}).get("listeComplements"))

            offre = Offres_FT(
                id=str(offer.get("id")),
                intitule=offer.get("intitule"),
                description=offer.get("description"),
                dateCreation=date_c,
                dateActualisation=date_a,
                romeCode=offer.get("romeCode"),
                romeLibelle=offer.get("romeLibelle"),
                appellationlibelle=offer.get("appellationlibelle"),
                typeContrat=offer.get("typeContrat"),
                typeContratLibelle=offer.get("typeContratLibelle"),
                natureContrat=offer.get("natureContrat"),
                experienceExige=offer.get("experienceExige"),
                experienceLibelle=offer.get("experienceLibelle"),
                
                # Champs ARRAY corrigés : on passe la liste, SQLAlchemy gère la conversion
                competences=competences_list, 
                formations=formations_list,
                langues=langues_list,
                permis=permis_list,
                qualitesProfessionnelles=qualites_list,
                salaire_listeComplements=salaire_comps_list,

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
                
                # Objets imbriqués aplatis
                lieuTravail_libelle=offer.get("lieuTravail", {}).get("libelle"),
                lieuTravail_latitude=str(offer.get("lieuTravail", {}).get("latitude")) if offer.get("lieuTravail", {}).get("latitude") else None,
                lieuTravail_longitude=str(offer.get("lieuTravail", {}).get("longitude")) if offer.get("lieuTravail", {}).get("longitude") else None,
                lieuTravail_codePostal=offer.get("lieuTravail", {}).get("codePostal"),
                lieuTravail_commune=offer.get("lieuTravail", {}).get("commune"),
                
                entreprise_nom=offer.get("entreprise", {}).get("nom"),
                entreprise_entrepriseAdaptee=offer.get("entreprise", {}).get("entrepriseAdaptee"),
                entreprise_description=offer.get("entreprise", {}).get("description"),
                entreprise_url=offer.get("entreprise", {}).get("url"),
                entreprise_logo=offer.get("entreprise", {}).get("logo"),
                
                salaire_libelle=offer.get("salaire", {}).get("libelle"),
                salaire_complement1=offer.get("salaire", {}).get("complement1"),
                salaire_commentaire=offer.get("salaire", {}).get("commentaire"),
                
                contact_nom=offer.get("contact", {}).get("nom"),
                contact_courriel=offer.get("contact", {}).get("courriel"),
                contact_urlPostulation=offer.get("contact", {}).get("urlPostulation"),
                
                origineOffre_origine=offer.get("origineOffre", {}).get("origine"),
                origineOffre_urlOrigine=offer.get("origineOffre", {}).get("urlOrigine"),
            )
            
            try:
                session.merge(offre) # Utilise merge au lieu de add pour éviter les doublons (update si existe)
                session.commit()
            except IntegrityError:
                session.rollback()
                continue
            except Exception as e:
                session.rollback()
                print(f"Erreur insertion offre {offer.get('id')}: {e}")

    except Exception as e:
        print(f"Erreur globale save: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    API_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"
    NB_OFFRE = 1000
    # Tes identifiants (Attention à ne pas les partager publiquement en prod)
    CLIENT_ID = "PAR_dux_dc80f0f45695a7c5d5baec8923f9fe0180cdfbf90d29c35307a8014e3275b200"
    CLIENT_SECRET = "20881cafb62205992dde84402208292faf4d976b01633d4f2d1e1e84adc5de48"
    AUTH_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token"

    print("🚀 Démarrage de l'import France Travail...")
    search_offers(API_URL, NB_OFFRE, CLIENT_ID, CLIENT_SECRET, AUTH_URL)
    print("✅ Import terminé.")