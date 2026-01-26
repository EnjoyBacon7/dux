import json
import logging
import asyncio
from server.models import User, Offres_FT
from server.config import settings
from server.utils.llm import call_llm_sync

logger = logging.getLogger(__name__)


class MatchingEngine:
    def __init__(self, db_session):
        self.db = db_session

        # Verify required configuration
        missing_vars = []
        if not settings.openai_api_key:
            missing_vars.append("openai_api_key")
        if not settings.openai_base_url:
            missing_vars.append("openai_base_url")
        if not settings.openai_model:
            missing_vars.append("openai_model")

        if missing_vars:
            error_msg = f"Configuration MatchingEngine incomplète. Variables manquantes : {', '.join(missing_vars)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def _generate_prompt(self, user: User, job: Offres_FT, lang: str = "fr") -> str:

        # Mapping des langues pour l'IA
        lang_map = {
            'fr': 'FRENCH', 'en': 'ENGLISH', 'es': 'SPANISH',
            'de': 'GERMAN', 'pt': 'PORTUGUESE', 'la': 'LATIN', 'auto': 'FRENCH'
        }
        target_lang = lang_map.get(lang.lower(), 'FRENCH')

        skills = ", ".join(user.skills) if user.skills else "Non renseigné"

        experiences_txt = "Aucune expérience listée."
        if user.experiences:
            experiences_txt = "\n".join([
                f"- {exp.title} chez {exp.company} ({exp.description or ''})"
                for exp in user.experiences
            ])

        job_skills = job.competences
        if isinstance(job_skills, str) and job_skills.strip().startswith("["):
            try:
                loaded = json.loads(job_skills)
                if isinstance(loaded, list) and len(loaded) > 0 and isinstance(loaded[0], dict):
                    job_skills = ", ".join([s.get('libelle', '') for s in loaded if s.get('libelle')])
            except (json.JSONDecodeError, TypeError, ValueError):
                pass

        # Instruction pour l'IA
        prompt = f"""
        Tu es un expert en recrutement multilingue.
        
        IMPORTANT: Provide the 'verdict', 'match_reasons', and 'missing_skills' values strictly in {target_lang}.
        (Keep the JSON keys in English, only translate the values).

        PROFIL CANDIDAT:
        - Titre: {user.headline or 'Non spécifié'}
        - Résumé: {user.summary or 'Non spécifié'}
        - Compétences: {skills}
        - Expériences: {experiences_txt}

        OFFRE D'EMPLOI:
        - Titre: {job.intitule}
        - Entreprise: {job.entreprise_nom}
        - Description: {job.description}
        - Compétences requises: {job_skills}

        TA MISSION:
        Analyse le matching et retourne UNIQUEMENT un JSON valide :
        {{
            "score_technique": (int 0-100),
            "score_culturel": (int 0-100),
            "match_reasons": ["Point 1 ({target_lang})", "Point 2 ({target_lang})"],
            "missing_skills": ["Compétence 1 ({target_lang})", "Compétence 2 ({target_lang})"],
            "verdict": "Synthèse courte et directe en {target_lang}."
        }}
        """
        return prompt

    def analyser_match(self, user: User, job: Offres_FT, lang: str = "fr") -> dict:
        """Exécute l'analyse"""
        logger.info(f"Analyse IA ({lang}) : {user.username} vs Job {job.id}")

        prompt = self._generate_prompt(user, job, lang)

        try:
            # Use unified LLM interface with JSON parsing
            result = call_llm_sync(
                prompt=prompt,
                system_content="Tu es un moteur de matching JSON strict.",
                temperature=0.2,
                max_tokens=800,
                parse_json=True
            )

            # Result is already parsed JSON from unified interface
            return result["data"]

        except ValueError as e:
            logger.error(f"Erreur analyse JSON: {e}")
            return {
                "score_technique": 0,
                "score_culturel": 0,
                "match_reasons": ["Erreur lors de l'analyse"],
                "missing_skills": [],
                "verdict": f"Erreur lors de l'analyse: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Erreur IA : {e}")
            return {
                "score_technique": 0,
                "score_culturel": 0,
                "match_reasons": ["Erreur IA"],
                "missing_skills": [],
                "verdict": f"Impossible d'analyser. ({str(e)})"
            }
