import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from sqlalchemy.orm import Session

# ✅ Import depuis models.py
from server.models import Fiche_Metier_ROME

load_dotenv()

CHROMA_PATH = "chroma_db"
embeddings = OpenAIEmbeddings()

vectorstore = Chroma(
    persist_directory=CHROMA_PATH,
    embedding_function=embeddings,
    collection_name="candidats_cvs"
)

def get_llm():
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    base_url = os.getenv("OPENAI_BASE_URL", None)
    return ChatOpenAI(model=model_name, base_url=base_url, temperature=0)

def get_vectorstore_retriever(user_id, k=4):
    return vectorstore.as_retriever(
        search_kwargs={"k": k, "filter": {"user_id": str(user_id)}}
    )

def enrichir_requete_avec_ref(db: Session, titre_offre, description_offre):
    # On récupère les fiches ROME (Format JSON)
    fiches = db.query(Fiche_Metier_ROME).all()
    
    if not fiches:
        return description_offre

    mots_inutiles = ["le", "la", "les", "de", "du", "des", "et", "ou", "pour", "h/f", "(h/f)"]
    mots_offre = [m for m in titre_offre.lower().replace("/", " ").split() if len(m) > 3 and m not in mots_inutiles]
    
    meilleur_match = None
    meilleur_score = 0
    competences_trouvees = []

    for fiche in fiches:
        # Structure du JSON : fiche.metier = {'code': 'M1805', 'libelle': 'Études et développement...'}
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