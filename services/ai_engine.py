import os
import shutil
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
# ✅ On utilise le modèle local pour les embeddings (gratuit et compatible)
from langchain_huggingface import HuggingFaceEmbeddings 
from langchain_chroma import Chroma
# ✅ Nouvel import nécessaire pour créer le profil virtuel
from langchain_core.documents import Document 
from langchain_community.document_loaders import PyPDFLoader
from sqlalchemy.orm import Session

from server.models import Fiche_Metier_ROME

load_dotenv()

CHROMA_PATH = "chroma_db"

# Configuration du modèle d'embedding local
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

vectorstore = Chroma(
    persist_directory=CHROMA_PATH,
    embedding_function=embeddings,
    collection_name="candidats_cvs"
)

def get_llm():
    """Récupère le modèle de Chat (GPT-4o ou OSS)"""
    model_name = os.getenv("OPENAI_MODEL", "gpt-oss-120b")
    base_url = os.getenv("OPENAI_BASE_URL", None)
    return ChatOpenAI(model=model_name, base_url=base_url, temperature=0)

def get_vectorstore_retriever(user_id, k=4):
    """Récupère le retriever filtré pour un utilisateur"""
    return vectorstore.as_retriever(
        search_kwargs={"k": k, "filter": {"user_id": str(user_id)}}
    )

def ajouter_cv_vectoriel(file_path, user_id, nom):
    """Lit un PDF et l'ajoute dans ChromaDB (Preuve factuelle)"""
    try:
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        for doc in pages:
            doc.metadata["user_id"] = str(user_id)
            doc.metadata["nom"] = nom
            doc.metadata["type"] = "cv_pdf" # Utile pour distinguer
        
        vectorstore.add_documents(pages)
        print(f"✅ CV PDF vectorisé avec succès pour {nom} ({len(pages)} pages)")
        return True
    except Exception as e:
        print(f"❌ Erreur vectorisation PDF: {e}")
        return False

# 👇 LA NOUVELLE FONCTION AJOUTÉE 👇
def ajouter_profil_vectoriel(user_id, nom, headline, summary, skills):
    """
    Crée un document virtuel avec les infos déclaratives et l'ajoute à ChromaDB.
    (Intention et Résumé)
    """
    try:
        # On construit un texte riche qui résume le profil
        texte_profil = f"""
        PROFIL CANDIDAT : {nom}
        TITRE : {headline or 'Non renseigné'}
        RÉSUMÉ : {summary or 'Non renseigné'}
        COMPÉTENCES DÉCLARÉES : {', '.join(skills) if skills else 'Aucune'}
        """
        
        # On crée un Document LangChain
        doc = Document(
            page_content=texte_profil,
            metadata={
                "user_id": str(user_id),
                "nom": nom,
                "type": "profil_declaratif", # Pour le distinguer du CV PDF
                "source": "formulaire_inscription"
            }
        )
        
        # On l'ajoute à la base vectorielle
        vectorstore.add_documents([doc])
        print(f"✅ Profil déclaratif vectorisé pour {nom}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur vectorisation profil: {e}")
        return False

def enrichir_requete_avec_ref(db: Session, titre_offre, description_offre):
    """Enrichit la description de l'offre avec les compétences du ROME"""
    fiches = db.query(Fiche_Metier_ROME).all()
    
    if not fiches:
        return description_offre

    mots_inutiles = ["le", "la", "les", "de", "du", "des", "et", "ou", "pour", "h/f", "(h/f)"]
    mots_offre = [m for m in titre_offre.lower().replace("/", " ").split() if len(m) > 3 and m not in mots_inutiles]
    
    meilleur_match = None
    meilleur_score = 0
    competences_trouvees = []

    for fiche in fiches:
        libelle_metier = fiche.metier.get('libelle', '').lower()
        score = 0
        for mot in mots_offre:
            if mot in libelle_metier:
                score += 1
        
        if titre_offre.lower() in libelle_metier:
            score += 5

        if score > meilleur_score:
            meilleur_score = score
            meilleur_match = libelle_metier
            comps = []
            savoirs = fiche.groupesSavoirs or []
            for groupe in savoirs:
                for savoir in groupe.get('savoirs', []):
                    comps.append(savoir.get('libelle'))
            competences_trouvees = comps[:20]

    if meilleur_match and meilleur_score > 0 and competences_trouvees:
        enrichissement = f"\n\n(CONTEXTE ROME - Le métier '{meilleur_match}' implique : {', '.join(filter(None, competences_trouvees))})"
        return description_offre + enrichissement
            
    return description_offre