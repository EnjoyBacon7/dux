import json
import logging
from typing import Optional, Dict, Any

from server.models import User, Offres_FT
from server.config import settings
from server.utils.llm import call_llm_sync
from server.utils.prompts import load_prompt_template

logger = logging.getLogger(__name__)

class MatchingEngine:
    def __init__(self, db_session):
        self.db = db_session

        # Vérification de la configuration
        missing_vars = []
        if not settings.openai_api_key:
            missing_vars.append("openai_api_key")
        if not settings.openai_model:
            missing_vars.append("openai_model")

        if missing_vars:
            error_msg = f"Configuration MatchingEngine incomplète. Variables manquantes : {', '.join(missing_vars)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def _generate_prompt(self, user: User, job: Offres_FT, lang: str = "fr") -> str:
        """
        Génère le prompt pour le LLM.
        Stratégie nettoyée :
        1. Utilise user.cv_text (Texte brut en BDD) -> Approche principale.
        2. En dernier recours, utilise les champs structurés legacy (user.experiences, etc.).
        """
        
        # --- ÉTAPE 1 : Extraction des données du Candidat ---
        
        # CAS A : Utilisation directe du texte brut en BDD
        if user.cv_text and len(user.cv_text.strip()) > 10:
            logger.info(f"MATCHING : Utilisation du cv_text brut pour User ID {user.id}")
            
            headline = user.headline or "Candidat"
            summary = "Voir le contenu complet du CV ci-dessous."
            skills = "Voir le contenu complet du CV ci-dessous."
            
            # On injecte tout le texte brut ici.
            experiences_txt = f"--- DÉBUT DU CONTENU BRUT DU CV ---\n{user.cv_text}\n--- FIN DU CONTENU BRUT ---"

        # CAS B : Fallback (Legacy) - Pas de texte brut, on utilise les anciennes colonnes
        else:
            logger.warning(f"User ID {user.id} n'a pas de cv_text. Utilisation des champs structurés (plus lent/moins précis).")
            headline = user.headline or 'Non spécifié'
            summary = user.summary or 'Non spécifié'
            skills = ", ".join(user.skills) if user.skills else "Non renseigné"
            
            experiences_txt = "Aucune expérience listée."
            if user.experiences:
                experiences_txt = "\n".join([
                    f"- {exp.title} chez {exp.company} ({exp.description or ''})" 
                    for exp in user.experiences
                ])

        # Additional matching context provided by user
        additional_context = ""
        if user.matching_context and len(user.matching_context.strip()) > 0:
            additional_context = f"\n\nCONTEXTE SUPPLÉMENTAIRE FOURNI PAR LE CANDIDAT:\n{user.matching_context}"

        # --- ÉTAPE 2 : Traitement de l'Offre (Job) ---
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

        # --- ÉTAPE 3 : Formatage du Prompt ---
        lang_map = {
            'fr': 'FRENCH', 'en': 'ENGLISH', 'es': 'SPANISH',
            'de': 'GERMAN', 'pt': 'PORTUGUESE', 'auto': 'FRENCH'
        }
        target_lang = lang_map.get(lang.lower(), 'FRENCH')

        template = load_prompt_template("profile_match_template")
        
        prompt = template.format(
            target_lang=target_lang,
            headline=headline,
            summary=summary,
            skills=skills,
            experiences=experiences_txt,
            job_title=job.intitule,
            company_name=job.entreprise_nom,
            job_description=job.description,
            job_skills=job_skills,
            additional_context=additional_context
        )
        return prompt

    def analyser_match(self, user: User, job: Offres_FT, lang: str = "fr") -> dict:
        """
        Exécute l'analyse de matching.
        """
        try:
            prompt = self._generate_prompt(user, job, lang)

            # Appel au LLM via l'interface unifiée
            result = call_llm_sync(
                prompt=prompt,
                system_content="Tu es un moteur de matching JSON strict.",
                temperature=0.2,
                max_tokens=1000,
                parse_json=True
            )

            return result["data"]

        except ValueError as e:
            logger.error(f"Erreur de parsing JSON LLM: {e}")
            return {
                "score_technique": 0,
                "score_culturel": 0,
                "match_reasons": ["Erreur de formatage de la réponse IA"],
                "missing_skills": [],
                "verdict": "Erreur technique lors de l'analyse."
            }
        except Exception as e:
            logger.error(f"Erreur Générale MatchingEngine : {e}", exc_info=True)
            return {
                "score_technique": 0,
                "score_culturel": 0,
                "match_reasons": ["Erreur interne"],
                "missing_skills": [],
                "verdict": f"Impossible d'analyser le profil. ({str(e)})"
            }