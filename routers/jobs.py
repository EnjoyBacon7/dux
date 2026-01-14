from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

# ✅ Imports corrects selon leur structure
from server.database import get_db_session  # La connexion
from server.models import User, Offres_FT   # Les données (déplacées dans models.py)
from services.matching_engine import MatchingEngine

router = APIRouter(prefix="/jobs", tags=["Jobs & Matching"])

# On utilise Depends(get_db_session) qui est défini dans leur fichier
@router.get("/match/{user_id}")
async def match_user_jobs(user_id: int, db: Session = Depends(get_db_session)):
    """
    Lance le matching pour un utilisateur spécifique contre les offres FT.
    """
    # 1. Récupérer l'utilisateur
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    # 2. Récupérer les offres
    offres = db.query(Offres_FT).limit(50).all()
    
    if not offres:
        return {"message": "Aucune offre dans la base de données."}

    # 3. Lancer le moteur
    engine = MatchingEngine(db)
    resultats = []

    print(f"🎯 Lancement du Matching pour {user.first_name} {user.last_name}...")

    for offre in offres:
        evaluation = engine.analyser_match(user, offre)
        
        score = evaluation['score_global_final']
        
        if score >= 0:
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

    # Tri par score décroissant
    resultats_tries = sorted(resultats, key=lambda x: x['scores']['final'], reverse=True)

    return {
        "candidat": f"{user.first_name} {user.last_name}",
        "recommandations": resultats_tries[:10]
    }