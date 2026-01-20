import os
import json
import logging
from openai import OpenAI
from server.models import User, Offres_FT

# Configuration du logger
logger = logging.getLogger(__name__)

class MatchingEngine:
    def __init__(self, db_session):
        """
        Initialize the MatchingEngine with a database session and configure an OpenAI-compatible client from environment variables.
        
        Reads OPENAI_API_KEY, OPENAI_BASE_URL and OPENAI_MODEL from the environment, stores them on the instance, and attempts to construct an OpenAI-compatible client; if client initialization fails the `client` attribute is set to None and the error is logged.
        
        Parameters:
            db_session: Database session or connection used by the engine for persistence and lookups.
        """
        self.db = db_session
        # On récupère la configuration depuis le .env
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL")
        self.model = os.getenv("OPENAI_MODEL")
        
        # Initialisation du client compatible OpenAI (pour Linagora/Mistral)
        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        except Exception as e:
            logger.error(f"Erreur init OpenAI: {e}")
            self.client = None

    def _generate_prompt(self, user: User, job: Offres_FT) -> str:
        """
        Builds a single textual prompt describing a candidate and a job offer for strict JSON matching by an AI.
        
        The prompt contains a candidate profile (title, summary, skills, experiences), a job offer block (title, company, description, required skills) and an instruction to return ONLY a valid JSON with the exact structure:
        {
          "score_technique": integer 0-100,
          "score_culturel": integer 0-100,
          "match_reasons": [string, ...],
          "missing_skills": [string, ...],
          "verdict": "short synthesis sentence"
        }
        Job required skills are normalized when stored as a JSON string (attempts to extract readable labels).
        
        Returns:
            prompt (str): The assembled multi-line prompt to send to the AI.
        """
        
        # 1. Préparation du Profil Candidat
        skills = ", ".join(user.skills) if user.skills else "Non renseigné"
        
        experiences_txt = "Aucune expérience listée."
        # Note: Tes expériences sont stockées dans une table liée, on assume que l'ORM les charge
        if hasattr(user, 'experiences') and user.experiences:
            experiences_txt = "\n".join([
                f"- {exp.title} chez {exp.company} ({exp.description or ''})" 
                for exp in user.experiences
            ])
            
        # 2. Préparation de l'Offre (Nettoyage des JSON stockés en string)
        job_skills = job.competences
        # Si c'est du JSON stringifié par pull_france_travail, on essaie de le rendre lisible
        if isinstance(job_skills, str) and job_skills.startswith("["):
            try:
                loaded = json.loads(job_skills)
                # France Travail renvoie souvent des objets {libelle: "...", ...}
                if isinstance(loaded, list) and len(loaded) > 0 and isinstance(loaded[0], dict):
                    job_skills = ", ".join([s.get('libelle', '') for s in loaded])
            except:
                pass # On garde la string brute si ça échoue

        prompt = f"""
        Tu es un expert en recrutement. Analyse la compatibilité (matching) entre ce candidat et cette offre.

        PROFIL CANDIDAT:
        - Titre: {user.headline or 'Non spécifié'}
        - Résumé: {user.summary or 'Non spécifié'}
        - Compétences: {skills}
        - Expériences:
        {experiences_txt}

        OFFRE D'EMPLOI:
        - Titre: {job.intitule}
        - Entreprise: {job.entreprise_nom}
        - Description: {job.description}
        - Compétences requises: {job_skills}

        TA MISSION:
        Retourne UNIQUEMENT un JSON valide (sans markdown ```json) avec cette structure exacte :
        {{
            "score_technique": (entier 0-100),
            "score_culturel": (entier 0-100, estimation basée sur le ton),
            "match_reasons": ["Point fort 1", "Point fort 2"],
            "missing_skills": ["Compétence manquante 1", "Compétence manquante 2"],
            "verdict": "Phrase de synthèse courte et directe."
        }}
        """
        return prompt

    def analyser_match(self, user: User, job: Offres_FT) -> dict:
        """
        Analyze a candidate and a job offer with the configured AI client and return a structured matching result.
        
        Sends a prompt describing the candidate and the job to the AI model and parses the model's JSON response into a dictionary with a fixed schema. If the AI client is not initialized the function raises an exception; on other errors it returns a safe default structure.
        
        Raises:
            Exception: If the AI client is not initialized (check environment/config).
        
        Returns:
            dict: Matching result with the following keys:
                - "score_technique" (int): Technical fit score from 0 to 100.
                - "score_culturel" (int): Cultural fit score from 0 to 100.
                - "match_reasons" (list[str]): Array of short reasons supporting the match.
                - "missing_skills" (list[str]): Array of skills missing for the candidate.
                - "verdict" (str): Short synthesis sentence summarizing the outcome.
        """
        logger.info(f" Analyse IA : {user.username} vs Job {job.id}")
        
        if not self.client:
            raise Exception("Client IA non initialisé (vérifier .env)")

        prompt = self._generate_prompt(user, job)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Tu es un moteur de matching JSON strict."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=800
            )
            
            content = response.choices[0].message.content.strip()
            
            # Nettoyage Markdown éventuel
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "")
            elif content.startswith("```"):
                content = content.replace("```", "")
            
            return json.loads(content)

        except Exception as e:
            logger.error(f" Erreur IA : {e}")
            # En cas d'erreur critique, on renvoie une structure vide pour ne pas crasher le front
            return {
                "score_technique": 0,
                "score_culturel": 0,
                "match_reasons": ["Erreur lors de l'analyse IA"],
                "missing_skills": [],
                "verdict": f"Impossible d'analyser l'offre pour le moment. ({str(e)})"
            }