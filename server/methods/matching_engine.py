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

    def _generate_prompt(self, user: User, job: Offres_FT, cv_data: Optional[Dict[str, Any]] = None, lang: str = "fr") -> str:
        """
        Génère le prompt pour le LLM.
        Si cv_data est fourni (dict), on l'utilise pour extraire compétences et expériences.
        Sinon, on utilise les attributs de l'objet User (base de données).
        """
        
        # --- ÉTAPE 1 : Extraction des données du Candidat ---
        if cv_data:
            # CAS A : Données fraîches du CV (Prioritaire)
            logger.info("Génération du prompt à partir des données brutes du CV (cv_data).")
            
            # Titre et Résumé
            personal_info = cv_data.get('personal_info', {}) or {}
            headline = personal_info.get('title') or "Candidat"
            
            summary_obj = cv_data.get('professional_summary')
            if isinstance(summary_obj, dict):
                summary = summary_obj.get('text', "Non spécifié")
            elif isinstance(summary_obj, str):
                summary = summary_obj
            else:
                summary = "Non spécifié"

            # Compétences (Aplatir la structure par catégories)
            skills_list = []
            raw_skills = cv_data.get('skills', [])
            if raw_skills:
                for cat in raw_skills:
                    if isinstance(cat, dict):
                        # Gérer le cas où 'skills' est une liste de strings dans la catégorie
                        cat_skills = cat.get('skills', [])
                        if isinstance(cat_skills, list):
                            skills_list.extend([str(s) for s in cat_skills])
            
            # Dédoublonnage et conversion en string
            skills = ", ".join(list(set(skills_list))) if skills_list else "Non renseigné"

            # Expériences
            experiences_list = []
            raw_exp = cv_data.get('work_experience', [])
            if raw_exp:
                for exp in raw_exp:
                    role = exp.get('role', 'Poste inconnu')
                    company = exp.get('company', 'Entreprise inconnue')
                    
                    # Gestion des responsabilités (liste ou string)
                    resps = exp.get('responsibilities', [])
                    desc = ""
                    if isinstance(resps, list):
                        desc = "; ".join(resps)
                    elif isinstance(resps, str):
                        desc = resps
                        
                    experiences_list.append(f"- {role} chez {company} ({desc})")
            
            experiences_txt = "\n".join(experiences_list) if experiences_list else "Aucune expérience listée."

        else:
            # CAS B : Données de la Base de Données (Fallback)
            logger.info("Génération du prompt à partir du profil User en BDD.")
            headline = user.headline or 'Non spécifié'
            summary = user.summary or 'Non spécifié'
            skills = ", ".join(user.skills) if user.skills else "Non renseigné"
            
            experiences_txt = "Aucune expérience listée."
            if user.experiences:
                experiences_txt = "\n".join([
                    f"- {exp.title} chez {exp.company} ({exp.description or ''})" 
                    for exp in user.experiences
                ])

        # --- ÉTAPE 2 : Traitement de l'Offre (Job) ---
        job_skills = job.competences
        # Gestion des différents formats possibles de job.competences (JSON string, list, None)
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

        # Chargement du template (assure-toi que "profile_match_template" existe dans prompts.py)
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
            job_skills=job_skills
        )
        return prompt

    def analyser_match(self, user: User, job: Offres_FT, cv_data: Optional[Dict[str, Any]] = None, lang: str = "fr") -> dict:
        """
        Exécute l'analyse de matching.
        
        Args:
            user: L'objet User (utilisé pour le logging et fallback si cv_data est None)
            job: L'objet Offres_FT
            cv_data: (Optionnel) Dictionnaire contenant les données extraites du CV.
                     Si fourni, le matching se base sur ces données et ignore la BDD User.
            lang: Langue de sortie souhaitée
        """
        try:
            prompt = self._generate_prompt(user, job, cv_data, lang)

            # DEBUG : Pour vérifier que les infos du CV sont bien là
            print("\n" + "="*50)
            print(f"MODE MATCHING : {'CV TEMPS RÉEL' if cv_data else 'PROFIL BDD'}")
            print("----- DÉBUT DU PROMPT ENVOYÉ À L'IA -----")
            print(prompt)
            print("----- FIN DU PROMPT -----")
            print("="*50 + "\n")

            # Appel au LLM via l'interface unifiée
            result = call_llm_sync(
                prompt=prompt,
                system_content="Tu es un moteur de matching JSON strict.",
                temperature=0.2,
                max_tokens=1000,
                parse_json=True
            )

            # result["data"] contient déjà le JSON parsé grâce à parse_json=True
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