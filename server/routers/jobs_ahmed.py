from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List

# Nos imports locaux
from server.database import get_db_session
from server.models import User, Offres_FT
from services.matching_engine import MatchingEngine

router = APIRouter(prefix="/jobs", tags=["Jobs & Matching"])

def extraire_mots_cles(user: User):
    keywords = set()
    
    # 1. Mots du titre (Headline)
    if user.headline:
        stop_words = ["le", "la", "les", "de", "du", "des", "un", "une", "et", "ou", "a", "pour", "h/f", "(h/f)", "senior", "junior", "je", "suis", "recherche"]
        mots_titre = [m.lower() for m in user.headline.replace("/", " ").replace("-", " ").split() if len(m) > 2]
        for mot in mots_titre:
            if mot not in stop_words:
                keywords.add(mot)

    # 2. Compétences (Skills)
    if user.skills:
        for skill in user.skills:
            keywords.add(skill.lower())

    return list(keywords)

@router.get("/match/{user_id}")
async def match_user_jobs(user_id: int, db: Session = Depends(get_db_session)):
    
    # 1. Récupérer l'utilisateur
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    # 2. PRÉ-SÉLECTION SQL
    mots_cles = extraire_mots_cles(user)
    print(f"🔑 Mots-clés de recherche : {mots_cles}")

    if not mots_cles:
        # Fallback large si pas de mots-clés
        offres_candidates = db.query(Offres_FT).order_by(Offres_FT.dateCreation.desc()).limit(50).all()
    else:
        conditions = []
        for mot in mots_cles:
            # On cherche dans le titre
            conditions.append(Offres_FT.intitule.ilike(f"%{mot}%"))
            # On cherche dans les compétences (converties en string)
            conditions.append(func.array_to_string(Offres_FT.competences, ' ').ilike(f"%{mot}%"))

        # 🚀 MODIF 1 : On augmente la limite à 60 pour capturer les bonnes offres
        # même s'il y a du "bruit" avant.
        offres_candidates = db.query(Offres_FT).filter(or_(*conditions)).limit(60).all()

    print(f"🔍 Offres candidates (SQL) : {len(offres_candidates)}")

    # 3. SCORING IA
    engine = MatchingEngine(db)
    resultats = []

    for offre in offres_candidates:
        try:
            evaluation = engine.analyser_match(user, offre)
            score = evaluation['score_global_final']
            
            # On garde tout ce qui est analysé, le tri fera le reste
            resultats.append({
                "job_id": offre.id,
                "intitule": offre.intitule,
                "entreprise": offre.entreprise_nom,
                "scores": {
                    "technique": evaluation['score_technique'],
                    "experience": evaluation['score_experience'],
                    "final": score
                },
                "details": evaluation
            })
        except Exception as e:
            print(f"Erreur scoring offre {offre.id}: {e}")
            continue

    # 4. TRI & FILTRAGE FINAL
    # On trie par le score final (du plus grand au plus petit)
    resultats_tries = sorted(resultats, key=lambda x: x['scores']['final'], reverse=True)

    # 🚀 MODIF 2 : On ne renvoie que le TOP 5
    top_5 = resultats_tries[:5]

    return {
        "candidat": f"{user.first_name} {user.last_name}",
        "filtre_sql": f"{len(offres_candidates)} offres analysées sur {len(mots_cles)} mots-clés.",
        "recommandations": top_5
    }