import sys
import os

# Ajout du dossier parent au path pour trouver le dossier 'server'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.database import get_db_session
from server.models import User

def create_users():
    # On récupère une session DB
    db = next(get_db_session())
    
    print("👤 Création des utilisateurs de test...")

    # --- UTILISATEUR 1 : Le Développeur Python (Profil idéal pour ton offre de test) ---
    user_dev = User(
        username="dev_python",
        email="dev@test.com",
        first_name="Thomas",
        last_name="Anderson",
        headline="Développeur Backend Python / FastAPI",
        summary="Passionné par le code propre et les architectures performantes. 5 ans d'expérience.",
        location="Paris",
        # Important pour le matching :
        skills=["Python", "Django", "FastAPI", "PostgreSQL", "Docker", "Git"],
        # Simulation du texte extrait d'un PDF :
        cv_text="""
        EXPÉRIENCE PROFESSIONNELLE
        2020-2024 : Développeur Backend chez TechCorp. 
        - Développement d'API REST avec FastAPI et Python.
        - Optimisation des requêtes SQL sur PostgreSQL.
        - Mise en place de pipelines CI/CD avec Docker et GitHub Actions.
        
        FORMATION
        Master Informatique - Université de Paris.
        """
    )

    # --- UTILISATEUR 2 : Le Commercial (Profil qui ne devrait PAS matcher avec une offre dev) ---
    user_sales = User(
        username="sales_manager",
        email="sales@test.com",
        first_name="Sophie",
        last_name="Martin",
        headline="Business Developer & Sales Manager",
        summary="Expertise en négociation B2B et développement de portefeuille client.",
        location="Lyon",
        skills=["Vente B2B", "CRM", "Négociation", "Prospection", "Salesforce"],
        cv_text="""
        EXPÉRIENCE
        Responsable Commerciale - Vente de solutions logicielles.
        - Augmentation du CA de 20% sur le secteur Sud-Est.
        - Management d'une équipe de 5 commerciaux.
        - Utilisation quotidienne de Salesforce.
        """
    )

    # --- UTILISATEUR 3 : Le Junior (Profil potentiel mais score plus bas) ---
    user_junior = User(
        username="junior_dev",
        email="junior@test.com",
        first_name="Lucas",
        last_name="Petit",
        headline="Étudiant en Informatique - Recherche Alternance",
        summary="Motivé et curieux, je cherche ma première expérience pro.",
        location="Bordeaux",
        skills=["Python", "HTML", "CSS", "Java Basics"],
        cv_text="""
        FORMATION
        Licence Informatique en cours.
        Projets personnels : Création d'un site web en HTML/CSS. Petit script Python pour automatiser des fichiers.
        Stage de découverte de 1 mois en maintenance informatique.
        """
    )

    try:
        # On ajoute les utilisateurs (s'ils n'existent pas déjà via username unique)
        for user in [user_dev, user_sales, user_junior]:
            existing = db.query(User).filter(User.username == user.username).first()
            if not existing:
                db.add(user)
                db.commit() # On commit pour générer l'ID
                db.refresh(user) # On recharge pour récupérer l'ID généré
                print(f"✅ Utilisateur créé : {user.first_name} {user.last_name} (ID: {user.id})")
            else:
                print(f"⚠️ L'utilisateur {user.username} existe déjà (ID: {existing.id})")
                
    except Exception as e:
        print(f"❌ Erreur : {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_users()