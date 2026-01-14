import json
from services.ai_engine import get_vectorstore_retriever, get_llm, enrichir_requete_avec_ref

class MatchingEngine:
    def __init__(self):
        self.llm = get_llm()

    def analyser_match(self, user_id: str, candidat_infos: str, job: dict):
        """
        C'est ici que se trouve le CŒUR du système :
        1. Enrichissement ROME
        2. RAG (Recherche Vectorielle)
        3. Prompt Engineering
        4. Scoring
        """
        
        # 1. Enrichissement (Intelligence Métier)
        # On transforme "Dev" en "Dev + SQL + Java..."
        query_enrichie = enrichir_requete_avec_ref(job["titre"], job["description"])
        
        # 2. RAG (Recherche de preuves dans le CV)
        retriever = get_vectorstore_retriever(user_id, k=4)
        docs = retriever.invoke(query_enrichie)
        context_cv = "\n".join([d.page_content for d in docs])

        # 3. Le Prompt (Le Juge)
        # Note les doubles accolades {{ }} pour le JSON dans le f-string
        prompt = f"""
        Tu es un expert Recrutement IA. 
        Ton but est d'évaluer la compatibilité (Matching) entre un candidat et une offre.

        --- OFFRE ---
        TITRE : {job['titre']}
        DESCRIPTION : {job['description']}
        
        --- CANDIDAT ---
        INFOS : {candidat_infos}
        PREUVES TROUVÉES DANS LE CV (Extrait) :
        {context_cv}
        
        --- INSTRUCTIONS ---
        Note sur 3 axes (0 à 100) :
        1. Technique (Hard Skills) : Les compétences clés sont-elles présentes ? (Pénalise fort si absent)
        2. Expérience : La séniorité correspond-elle ?
        3. Global : Cohérence générale (Soft skills, localisation, motivation...)

        Donne ta réponse UNIQUEMENT au format JSON strict suivant :
        {{
            "score_technique": int,
            "score_experience": int,
            "score_global_final": int,
            "points_manquants": ["point 1", "point 2"],
            "verdict": "explication courte et percutante"
        }}
        """

        # 4. Exécution et Parsing
        try:
            response = self.llm.invoke(prompt)
            # Nettoyage classique du markdown json
            content_clean = response.content.replace("```json", "").replace("```", "").strip()
            return json.loads(content_clean)
        except Exception as e:
            print(f"❌ Erreur Scoring pour {job['titre']}: {e}")
            # En cas d'erreur, on retourne une note neutre ou nulle pour ne pas casser la boucle
            return {
                "score_technique": 0, 
                "score_experience": 0, 
                "score_global_final": -1, # Code d'erreur
                "points_manquants": ["Erreur analyse IA"],
                "verdict": "Erreur technique"
            }