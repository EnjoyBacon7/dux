import json
from sqlalchemy.orm import Session
from services.ai_engine import get_llm, enrichir_requete_avec_ref, get_vectorstore_retriever

# ✅ Import depuis models.py
from server.models import User, Offres_FT

class MatchingEngine:
    def __init__(self, db: Session):
        self.db = db
        self.llm = get_llm()

    def analyser_match(self, user: User, offre: Offres_FT):
        
        # 1. Enrichissement ROME
        query_enrichie = enrichir_requete_avec_ref(self.db, offre.intitule, offre.description)
        
        # 2. RAG (Recherche dans le CV vectorisé)
        # user.id est un int, on le convertit en str pour ChromaDB
        retriever = get_vectorstore_retriever(str(user.id), k=4)
        docs = retriever.invoke(query_enrichie)
        context_cv = "\n".join([d.page_content for d in docs])

        # Construction du profil candidat
        infos_candidat = f"Nom: {user.first_name} {user.last_name}\n"
        infos_candidat += f"Titre: {user.headline}\n"
        infos_candidat += f"Résumé: {user.summary}\n"
        if user.skills:
            # skills est un ARRAY dans Postgres, Python le voit comme une liste
            infos_candidat += f"Compétences déclarées: {', '.join(user.skills)}\n"

        # 3. Prompt
        prompt = f"""
        Tu es un expert Recrutement IA. 
        Évalue la compatibilité entre ce candidat et cette offre France Travail.

        --- OFFRE ---
        INTITULÉ : {offre.intitule}
        DESCRIPTION : {offre.description}
        LIEU : {offre.lieuTravail_libelle}
        CONTRAT : {offre.typeContratLibelle}
        
        --- CANDIDAT ---
        PROFIL : {infos_candidat}
        EXTRAITS DU CV (Preuves) :
        {context_cv}
        
        --- INSTRUCTIONS ---
        Note sur 3 axes (0 à 100) :
        1. Technique : Compétences clés présentes ?
        2. Expérience : Séniorité correspondante ?
        3. Global : Cohérence générale.

        Donne ta réponse UNIQUEMENT au format JSON strict :
        {{
            "score_technique": int,
            "score_experience": int,
            "score_global_final": int,
            "points_manquants": ["point 1", "point 2"],
            "verdict": "explication courte"
        }}
        """

        try:
            response = self.llm.invoke(prompt)
            content_clean = response.content.replace("```json", "").replace("```", "").strip()
            return json.loads(content_clean)
        except Exception as e:
            print(f"❌ Erreur Scoring: {e}")
            return {
                "score_technique": 0, 
                "score_experience": 0, 
                "score_global_final": -1,
                "points_manquants": ["Erreur IA"],
                "verdict": "Erreur technique"
            }