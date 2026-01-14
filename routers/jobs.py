import json
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# --- IMPORTS MODULAIRES ---
from database.db import get_db_connection
from psycopg2.extras import RealDictCursor

# ✅ NOUVEAU : On importe uniquement le moteur de scoring
from services.matching_engine import MatchingEngine

# On garde ces imports pour la route de test "/analyze/" qui n'utilise pas encore le moteur
from services.ai_engine import get_vectorstore_retriever, get_llm, enrichir_requete_avec_ref

router = APIRouter(prefix="/jobs", tags=["Offres d'emploi"])

# ---------------------------------------------------------
# 1. LISTER TOUTES LES OFFRES (Standard)
# ---------------------------------------------------------
@router.get("/")
async def lister_toutes_les_offres():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM jobs ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    resultats = []
    for row in rows:
        desc = row["description"]
        resultats.append({
            "id": row["id"],
            "titre": row["titre"],
            "ville": row["ville"],
            "contrat": row["type_contrat"],
            "salaire": row["salaire"],
            "description_courte": (desc[:150] + "...") if desc and len(desc) > 150 else (desc or "")
        })

    return {"total": len(resultats), "offres": resultats}

# ---------------------------------------------------------
# 2. AJOUTER UNE OFFRE (Standard)
# ---------------------------------------------------------
@router.post("/add/")
async def ajouter_job(job: dict): 
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO jobs (titre, description, ville, type_contrat, salaire) 
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (job["titre"], job["description"], job.get("ville"), job.get("type_contrat"), job.get("salaire")))
        
        new_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        return {"message": f"Offre '{job['titre']}' ajoutée !", "id": new_id}
    except Exception as e:
        conn.rollback()
        conn.close()
        return {"error": str(e)}

# ---------------------------------------------------------
# 3. RECHERCHE (Standard)
# ---------------------------------------------------------
@router.get("/search/")
async def rechercher_jobs(q: Optional[str] = None, ville: Optional[str] = None, contrat: Optional[str] = None):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = "SELECT * FROM jobs WHERE 1=1"
    params = []

    if q:
        nettoye = q.replace(",", " ")
        mots_cles = nettoye.split()
        if mots_cles:
            conditions = []
            for mot in mots_cles:
                conditions.append("(titre ILIKE %s OR description ILIKE %s)")
                params.extend([f"%{mot}%", f"%{mot}%"])
            query += " AND (" + " OR ".join(conditions) + ")"

    if ville:
        query += " AND ville ILIKE %s"
        params.append(f"%{ville}%")

    if contrat:
        query += " AND type_contrat ILIKE %s"
        params.append(f"%{contrat}%")

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()

    return {"recherche": q, "nombre_resultats": len(rows), "resultats": rows}

# ---------------------------------------------------------
# 4. MATCHING INTELLIGENT (UTILISE LE NOUVEAU MOTEUR) 🧠
# ---------------------------------------------------------
@router.get("/match/{user_id}")
async def trouver_jobs_pour_candidat(user_id: str):
    # A. Récupération des données SQL
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT nom, infos FROM candidats WHERE id = %s", (user_id,))
    candidat = cursor.fetchone()
    
    cursor.execute("SELECT id, titre, description FROM jobs")
    all_jobs = cursor.fetchall()
    conn.close()

    if not candidat:
        raise HTTPException(status_code=404, detail="Candidat introuvable")
    
    # B. Appel du Moteur de Scoring
    # On instancie la classe que tu as créée dans l'étape précédente
    engine = MatchingEngine()
    resultats = []
    
    print(f"🎯 MatchingEngine activé pour {candidat['nom']}...")

    for job in all_jobs:
        # C'est ici que la magie opère : une seule ligne pour tout faire !
        evaluation = engine.analyser_match(user_id, candidat["infos"], job)
        
        score_final = evaluation['score_global_final']
        
        # On filtre les erreurs (-1)
        if score_final >= 0:
            print(f"   📊 {job['titre']} -> {score_final}/100")
            resultats.append({
                "job_id": job["id"],
                "titre": job["titre"],
                "scores": {
                    "technique": evaluation['score_technique'],
                    "experience": evaluation['score_experience'],
                    "final": score_final
                },
                "details": {
                    "manque": evaluation['points_manquants'],
                    "avis": evaluation['verdict']
                }
            })

    # Tri par pertinence
    resultats_tries = sorted(resultats, key=lambda x: x['scores']['final'], reverse=True)
    
    return {
        "candidat": candidat["nom"],
        "systeme": "MatchingEngine v1 (Postgres + ROME)",
        "recommandations": resultats_tries[:5]
    }

# ---------------------------------------------------------
# 5. ROUTE DE TEST ANALYSE (Gardée pour le Debug Swagger)
# ---------------------------------------------------------
class AnalyseRequest(BaseModel):
    user_id: str
    description_poste: str

@router.post("/analyze/")
async def analyser_description_poste(payload: AnalyseRequest):
    """
    Analyse "One-Shot" pour tester un texte sans créer d'offre en base.
    """
    user_id = payload.user_id
    description = payload.description_poste

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT nom, infos FROM candidats WHERE id = %s", (user_id,))
    candidat = cursor.fetchone()
    conn.close()

    if not candidat:
        raise HTTPException(status_code=404, detail="Candidat introuvable")

    # Logique simplifiée pour le test rapide
    titre_estime = description[:100]
    query_enrichie = enrichir_requete_avec_ref(titre_estime, description)
    retriever = get_vectorstore_retriever(user_id, k=4)
    docs = retriever.invoke(query_enrichie)
    context_cv = "\n".join([d.page_content for d in docs])

    model = get_llm()
    prompt = f"""
    Analyse RAPIDE.
    OFFRE: {description}
    CANDIDAT: {candidat['infos']}
    CV: {context_cv}
    
    JSON attendu: {{ "score": int, "avis": "str" }}
    """
    
    try:
        response = model.invoke(prompt)
        content = response.content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except Exception as e:
        return {"error": str(e)}