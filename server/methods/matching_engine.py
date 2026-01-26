import json
import logging
from openai import OpenAI
from server.models import User, Offres_FT
from server.config import settings
from server.utils.prompts import load_prompt_template

logger = logging.getLogger(__name__)

class MatchingEngine:
    def __init__(self, db_session):
        self.db = db_session
        self.api_key = settings.openai_api_key
        self.base_url = settings.openai_base_url
        self.model = settings.openai_model
        
        missing_vars = []
        if not self.api_key: missing_vars.append("openai_api_key")
        if not self.base_url: missing_vars.append("openai_base_url")
        if not self.model: missing_vars.append("openai_model")

        if missing_vars:
            error_msg = f"Configuration MatchingEngine incomplète. Variables manquantes : {', '.join(missing_vars)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        except Exception as e:
            logger.error(f"Erreur init OpenAI: {e}")
            raise ValueError(f"Impossible d'initialiser le client OpenAI : {e}")

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
        elif isinstance(job_skills, list):
            job_skills = ", ".join(str(s) for s in job_skills if s)
        elif job_skills is None:
            job_skills = "Non renseigné"

        # Load prompt template and format it
        template = load_prompt_template("profile_match_template")
        prompt = template.format(
            target_lang=target_lang,
            headline=user.headline or 'Non spécifié',
            summary=user.summary or 'Non spécifié',
            skills=skills,
            experiences=experiences_txt,
            job_title=job.intitule,
            company_name=job.entreprise_nom,
            job_description=job.description,
            job_skills=job_skills
        )
        return prompt

    def analyser_match(self, user: User, job: Offres_FT, lang: str = "fr") -> dict:
        """Exécute l'analyse"""
        logger.info(f"Analyse IA ({lang}) : {user.username} vs Job {job.id}")
        
        if not self.client:
            raise Exception("Client IA non initialisé")

        try:
            # Passage du paramètre lang - moved inside try block to catch FileNotFoundError
            prompt = self._generate_prompt(user, job, lang)
            
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
            if content.startswith("```json"): content = content.replace("```json", "").replace("```", "")
            elif content.startswith("```"): content = content.replace("```", "")
            
            return json.loads(content)

        except Exception as e:
            logger.error(f"Erreur IA : {e}")
            return {
                "score_technique": 0, "score_culturel": 0,
                "match_reasons": ["Erreur IA"], "missing_skills": [],
                "verdict": f"Impossible d'analyser. ({str(e)})"
            }