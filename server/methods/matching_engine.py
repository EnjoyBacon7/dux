import os
import json
import logging
from openai import OpenAI
from server.models import User, Offres_FT

# Configuration du logger
logger = logging.getLogger(__name__)

class MatchingEngine:
    def __init__(self, db_session):
        self.db = db_session
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL")
        self.model = os.getenv("OPENAI_MODEL")
        
        missing_vars = []
        if not self.api_key: missing_vars.append("OPENAI_API_KEY")
        if not self.base_url: missing_vars.append("OPENAI_BASE_URL")
        if not self.model: missing_vars.append("OPENAI_MODEL")

        if missing_vars:
            error_msg = f"Configuration MatchingEngine incomplète. Variables manquantes : {', '.join(missing_vars)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        # ---------------------------------

        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        except Exception as e:
            logger.error(f"Erreur init OpenAI: {e}")
            # On relève l'erreur pour ne pas démarrer avec un moteur cassé
            raise ValueError(f"Impossible d'initialiser le client OpenAI : {e}")

    def _generate_prompt(self, user: User, job: Offres_FT) -> str:
        skills = ", ".join(user.skills) if user.skills else "Non renseigné"
        
        experiences_txt = "Aucune expérience listée."
        if user.experiences:
            experiences_txt = "\n".join([
                f"- {exp.title} chez {exp.company} ({exp.description or ''})" 
                for exp in user.experiences
            ])
            
        job_skills = job.competences
        # Tentative de parsing si c'est une chaîne JSON (format France Travail)
        if isinstance(job_skills, str) and job_skills.strip().startswith("["):
            try:
                loaded = json.loads(job_skills)
                if isinstance(loaded, list) and len(loaded) > 0 and isinstance(loaded[0], dict):
                    # Extraction propre des libellés
                    job_skills = ", ".join([s.get('libelle', '') for s in loaded if s.get('libelle')])
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                # Log l'erreur avec le contexte (ID du job et début de la chaîne problématique)
                # On utilise warning car ce n'est pas bloquant (on garde la chaîne brute)
                logger.warning(
                    f" Erreur parsing JSON compétences pour Job {job.id}. "
                    f"Erreur: {e}. Raw Data (50 premiers chars): {job_skills[:50]}..."
                )
                # Fallback implicite : on garde job_skills tel quel

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
        """Exécute l'analyse"""
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