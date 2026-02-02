"""
Advisor (orientation / cover letter / CV tips) chat router.

Provides endpoints for advisor context, conversation CRUD, and chat with persistence.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Literal, Optional

import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from server.database import get_db_session, SessionLocal
from server.models import (
    User,
    CVEvaluation,
    FavouriteJob,
    AdvisorConversation,
    AdvisorMessage,
)
from server.utils.dependencies import get_current_user
from server.utils.llm import call_llm_messages_async, stream_llm_messages_async

router = APIRouter(prefix="/advisor", tags=["Advisor"])
logger = logging.getLogger(__name__)

# None = let frontend show localized "advisor.untitled"
DEFAULT_CONVERSATION_TITLE: Optional[str] = None
MAX_HISTORY_TURNS = 10
TITLE_SNIPPET_LENGTH = 50


# ============================================================================
# Request / Response models
# ============================================================================


class AdvisorContextResponse(BaseModel):
    hasCv: bool
    latestEvaluation: Optional[dict[str, Any]] = None
    favouriteJobs: list[dict[str, Any]]


class ConversationListItem(BaseModel):
    id: int
    title: Optional[str] = None
    updatedAt: Optional[str] = None


class ConversationCreatePayload(BaseModel):
    title: Optional[str] = None


class ConversationCreateResponse(BaseModel):
    id: int
    title: Optional[str] = None
    createdAt: Optional[str] = None


class MessageItem(BaseModel):
    role: str
    content: str
    createdAt: Optional[str] = None


class ConversationDetailResponse(BaseModel):
    id: int
    title: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    messages: list[MessageItem]


class ConversationPatchPayload(BaseModel):
    title: str


class ChatContextPayload(BaseModel):
    intent: Optional[str] = None  # "orientation" | "cover_letter" | "cv_tips"
    jobId: Optional[str] = None


class ChatMessageItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequestPayload(BaseModel):
    message: str
    conversationHistory: Optional[list[ChatMessageItem]] = None
    context: Optional[ChatContextPayload] = None
    conversationId: Optional[int] = None


class ChatResponse(BaseModel):
    reply: str
    conversationId: int


# ============================================================================
# Helpers
# ============================================================================


def _latest_evaluation_summary(db: Session, user_id: int) -> Optional[dict[str, Any]]:
    """Return a summary dict of the latest completed CV evaluation for the user."""
    ev = (
        db.query(CVEvaluation)
        .filter(
            CVEvaluation.user_id == user_id,
            CVEvaluation.evaluation_status == "completed",
        )
        .order_by(CVEvaluation.created_at.desc())
        .first()
    )
    if not ev:
        return None
    return {
        "overall_score": ev.overall_score,
        "overall_summary": ev.overall_summary,
        "strengths": ev.strengths or [],
        "weaknesses": ev.weaknesses or [],
        "recommendations": ev.recommendations or [],
        "red_flags": ev.red_flags or [],
        "missing_info": ev.missing_info or [],
    }


def _latest_structured_cv(db: Session, user_id: int) -> Optional[dict[str, Any]]:
    """Return the structured_cv JSON from the latest completed CV evaluation, or None."""
    ev = (
        db.query(CVEvaluation)
        .filter(
            CVEvaluation.user_id == user_id,
            CVEvaluation.evaluation_status == "completed",
            CVEvaluation.structured_cv.isnot(None),
        )
        .order_by(CVEvaluation.created_at.desc())
        .first()
    )
    if not ev or not ev.structured_cv:
        return None
    return ev.structured_cv


def _format_structured_cv_for_prompt(scv: dict[str, Any]) -> str:
    """Format structured CV dict into a clear, concise text for the LLM prompt."""
    lines: list[str] = []
    pi = scv.get("personal_info") or {}
    if isinstance(pi, dict):
        name = pi.get("name") or ""
        if name:
            lines.append(f"Nom : {name}")
        for key, label in [("email", "Email"), ("phone", "Téléphone"), ("location", "Lieu")]:
            if pi.get(key):
                lines.append(f"{label} : {pi[key]}")
    ps = scv.get("professional_summary")
    if ps and isinstance(ps, dict) and ps.get("text"):
        lines.append(f"Résumé professionnel : {ps['text']}")
    elif ps and isinstance(ps, str):
        lines.append(f"Résumé professionnel : {ps}")
    for we in scv.get("work_experience") or []:
        if not isinstance(we, dict):
            continue
        role = we.get("role") or ""
        company = we.get("company") or ""
        dates = " - ".join(filter(None, [we.get("start_date"), we.get("end_date")]))
        lines.append(f"  • {role} @ {company} ({dates})")
        for r in (we.get("responsibilities") or [])[:5]:
            if r:
                lines.append(f"    - {r}")
    if lines:
        lines.append("")
    lines.append("Formation :")
    for edu in scv.get("education") or []:
        if not isinstance(edu, dict):
            continue
        degree = edu.get("degree") or ""
        field = edu.get("field_of_study") or ""
        inst = edu.get("institution") or ""
        dates = " - ".join(filter(None, [edu.get("start_date"), edu.get("end_date")]))
        lines.append(f"  • {degree} {field} - {inst} ({dates})")
    if lines and lines[-1]:
        lines.append("")
    lines.append("Compétences :")
    for sk in scv.get("skills") or []:
        if not isinstance(sk, dict):
            continue
        cat = sk.get("category") or "Divers"
        skills_list = sk.get("skills") or []
        if skills_list:
            lines.append(f"  • {cat} : {', '.join(skills_list[:12])}")
    for proj in scv.get("projects") or []:
        if isinstance(proj, dict) and (proj.get("name") or proj.get("description")):
            lines.append(f"  • Projet : {proj.get('name', '')} - {proj.get('description', '') or ''}")
    for cert in scv.get("certifications") or []:
        if isinstance(cert, dict) and cert.get("name"):
            lines.append(f"  • Certification : {cert['name']}" + (f" ({cert.get('issuer')})" if cert.get("issuer") else ""))
    for lang in scv.get("languages") or []:
        if isinstance(lang, dict) and lang.get("language"):
            lines.append(f"  • Langue : {lang['language']}" + (f" ({lang.get('proficiency')})" if lang.get("proficiency") else ""))
    return "\n".join(lines).strip()


def _favourite_jobs_list(db: Session, user_id: int) -> list[dict[str, Any]]:
    """Return list of favourite jobs for the user (same shape as jobs router)."""
    rows = (
        db.query(FavouriteJob)
        .filter(FavouriteJob.user_id == user_id)
        .order_by(FavouriteJob.created_at.desc())
        .all()
    )
    return [
        {
            "jobId": r.job_id,
            "intitule": r.intitule or r.job_id,
            "entreprise_nom": r.entreprise_nom,
            "romeCode": r.rome_code,
            "addedAt": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


def _build_system_prompt(
    latest_eval: Optional[dict[str, Any]],
    intent: Optional[str],
    job_summary: Optional[str],
    structured_cv: Optional[dict[str, Any]] = None,
) -> str:
    """Build the advisor system prompt from CV evaluation, intent, optional job, and optional structured CV."""
    parts = [
        "Tu es un conseiller en orientation professionnelle. Tu aides les utilisateurs à :",
        "- Trouver la bonne orientation / métier (conseil en orientation).",
        "- Rédiger une lettre de motivation adaptée à une offre d'emploi.",
        "- Améliorer leur CV (conseils de rédaction, structure, contenu).",
        "Réponds toujours dans la langue de l'utilisateur (ou en français par défaut).",
        "Sois concis, bienveillant et concret.",
    ]
    if latest_eval:
        parts.append(
            "\n## Contexte CV du candidat (à utiliser pour l'orientation, les conseils CV et les lettres de motivation) :"
        )
        if latest_eval.get("overall_summary"):
            parts.append(f"- Résumé : {latest_eval['overall_summary']}")
        if latest_eval.get("strengths"):
            parts.append("- Points forts : " + "; ".join(latest_eval["strengths"][:8]))
        if latest_eval.get("weaknesses"):
            parts.append("- Points à améliorer : " + "; ".join(latest_eval["weaknesses"][:5]))
        if latest_eval.get("recommendations"):
            parts.append("- Recommandations : " + "; ".join(latest_eval["recommendations"][:5]))
        if latest_eval.get("red_flags"):
            parts.append("- Alertes : " + "; ".join(latest_eval["red_flags"][:3]))
        if latest_eval.get("missing_info"):
            parts.append("- Informations manquantes : " + "; ".join(latest_eval["missing_info"][:3]))
    if intent == "cover_letter" and structured_cv:
        formatted = _format_structured_cv_for_prompt(structured_cv)
        if formatted:
            parts.append("\n## Profil CV structuré du candidat (à utiliser pour personnaliser la lettre) :")
            parts.append(formatted)
    if intent == "cv_tips" and latest_eval:
        parts.append("\nL'utilisateur demande des conseils CV : utilise les recommandations et points faibles ci-dessus pour proposer des reformulations concrètes par section.")
    if intent == "cover_letter" and job_summary:
        parts.append("\n## Offre ciblée pour la lettre de motivation :")
        parts.append(job_summary)
        parts.append(
            "\nRédige une lettre de motivation personnalisée et détaillée pour cette offre. "
            "Instructions obligatoires : "
            "(1) Utilise les informations concrètes du CV ci-dessus (expériences, formations, compétences, réalisations) "
            "et cite-les dans la lettre pour montrer l'adéquation avec le poste. "
            "(2) Fais le lien explicite entre les exigences de l'offre et le profil du candidat. "
            "(3) Évite les formules génériques ; chaque paragraphe doit apporter un élément précis (exemple : projet, chiffre, compétence). "
            "(4) Structure : accroche qui lie le profil au poste, paragraphe sur la motivation et l'entreprise, paragraphe sur l'apport du candidat (expériences/compétences en lien avec l'offre), formule de politesse. "
            "La lettre doit refléter le profil réel du candidat et convaincre le recruteur par des arguments précis."
        )
    return "\n".join(parts)


def _job_offer_summary(job_data: dict[str, Any]) -> str:
    """Build a text summary of a job offer for the system prompt (enough detail to match CV)."""
    title = job_data.get("intitule") or "Sans intitulé"
    company = job_data.get("entreprise_nom") or ""
    desc = (job_data.get("description") or "")[:1800]
    return f"Intitulé : {title}. Entreprise : {company}. Description (extrait) : {desc}"


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/context", summary="Get advisor page context")
async def get_advisor_context(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> AdvisorContextResponse:
    """Return hasCv, latestEvaluation summary, and favouriteJobs for the advisor UI."""
    has_cv = bool(current_user.cv_filename)
    latest_eval = _latest_evaluation_summary(db, current_user.id)
    if latest_eval:
        has_cv = True
    favourite_jobs = _favourite_jobs_list(db, current_user.id)
    return AdvisorContextResponse(
        hasCv=has_cv,
        latestEvaluation=latest_eval,
        favouriteJobs=favourite_jobs,
    )


@router.get("/conversations", summary="List user's advisor conversations")
async def list_conversations(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[ConversationListItem]:
    """List conversations for the sidebar, ordered by updated_at desc."""
    rows = (
        db.query(AdvisorConversation)
        .filter(AdvisorConversation.user_id == current_user.id)
        .order_by(AdvisorConversation.updated_at.desc())
        .all()
    )
    return [
        ConversationListItem(
            id=r.id,
            title=r.title or None,
            updatedAt=r.updated_at.isoformat() if r.updated_at else None,
        )
        for r in rows
    ]


@router.post("/conversations", summary="Create a new conversation")
async def create_conversation(
    payload: ConversationCreatePayload,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ConversationCreateResponse:
    """Create a new conversation (e.g. when user clicks New chat)."""
    conv = AdvisorConversation(
        user_id=current_user.id,
        title=(payload.title and payload.title.strip()) or DEFAULT_CONVERSATION_TITLE,
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return ConversationCreateResponse(
        id=conv.id,
        title=conv.title,
        createdAt=conv.created_at.isoformat() if conv.created_at else None,
    )


def _conversation_for_user(db: Session, conversation_id: int, user_id: int) -> Optional[AdvisorConversation]:
    return (
        db.query(AdvisorConversation)
        .filter(
            AdvisorConversation.id == conversation_id,
            AdvisorConversation.user_id == user_id,
        )
        .first()
    )


@router.get("/conversations/{conversation_id}", summary="Get one conversation with messages")
async def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ConversationDetailResponse:
    """Get a single conversation and its messages (for loading a chat in the sidebar)."""
    conv = _conversation_for_user(db, conversation_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = [
        MessageItem(
            role=m.role,
            content=m.content,
            createdAt=m.created_at.isoformat() if m.created_at else None,
        )
        for m in conv.messages
    ]
    return ConversationDetailResponse(
        id=conv.id,
        title=conv.title,
        createdAt=conv.created_at.isoformat() if conv.created_at else None,
        updatedAt=conv.updated_at.isoformat() if conv.updated_at else None,
        messages=messages,
    )


@router.patch("/conversations/{conversation_id}", summary="Rename conversation")
async def patch_conversation(
    conversation_id: int,
    payload: ConversationPatchPayload,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ConversationListItem:
    """Update conversation title."""
    conv = _conversation_for_user(db, conversation_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    conv.title = (payload.title or "").strip() or (DEFAULT_CONVERSATION_TITLE or None)
    db.commit()
    db.refresh(conv)
    return ConversationListItem(
        id=conv.id,
        title=conv.title,
        updatedAt=conv.updated_at.isoformat() if conv.updated_at else None,
    )


@router.delete("/conversations/{conversation_id}", summary="Delete conversation")
async def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a conversation and all its messages."""
    conv = _conversation_for_user(db, conversation_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(conv)
    db.commit()
    return None


@router.post("/chat", summary="Send message and get advisor reply")
async def post_chat(
    payload: ChatRequestPayload,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    """Process user message, call LLM, persist messages, return reply and conversationId."""
    message = (payload.message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    # Resolve conversation (create if new chat)
    conversation_id = payload.conversationId
    conv = None
    if conversation_id:
        conv = _conversation_for_user(db, conversation_id, current_user.id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

    # Load CV evaluation summary and optional job offer
    latest_eval = _latest_evaluation_summary(db, current_user.id)
    job_summary = None
    if payload.context and payload.context.jobId:
        try:
            from server.methods.FT_job_search import get_offer_by_id
            from server.routers.jobs_router import _flatten_offer
            offer_data = await asyncio.to_thread(get_offer_by_id, payload.context.jobId)
            flat = _flatten_offer(offer_data)
            job_summary = _job_offer_summary(flat)
        except ValueError as e:
            logger.warning("Could not load job offer (jobId=%s): %s", payload.context.jobId, e)

    intent = payload.context.intent if payload.context else None
    structured_cv = _latest_structured_cv(db, current_user.id) if intent == "cover_letter" else None
    system_prompt = _build_system_prompt(
        latest_eval, intent, job_summary, structured_cv=structured_cv
    )

    # Build messages for LLM: system + history (last N) + new user message
    history = payload.conversationHistory or []
    history = history[-MAX_HISTORY_TURNS * 2 :]  # last N exchanges
    messages = [{"role": "system", "content": system_prompt}]
    for h in history:
        messages.append({"role": h.role, "content": h.content or ""})
    messages.append({"role": "user", "content": message})

    # Call LLM
    try:
        result = await call_llm_messages_async(
            messages,
            temperature=0.7,
            max_tokens=2000,
        )
    except ValueError as e:
        logger.exception(
            "Advisor LLM call failed (user_id=%s, conversation_id=%s)",
            current_user.id,
            conversation_id,
        )
        raise HTTPException(status_code=502, detail=str(e)) from e

    reply = result.get("data") or ""

    # Create conversation if new chat
    if not conv:
        conv = AdvisorConversation(
            user_id=current_user.id,
            title=DEFAULT_CONVERSATION_TITLE or None,
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)

    # Update title to first user message snippet if still default (None or empty)
    if not (conv.title or "").strip() and message:
        snippet = message[:TITLE_SNIPPET_LENGTH].strip()
        if snippet:
            conv.title = snippet + ("..." if len(message) > TITLE_SNIPPET_LENGTH else "")

    # Persist user and assistant messages
    user_msg = AdvisorMessage(conversation_id=conv.id, role="user", content=message)
    assistant_msg = AdvisorMessage(conversation_id=conv.id, role="assistant", content=reply)
    db.add(user_msg)
    db.add(assistant_msg)
    conv.updated_at = datetime.now(timezone.utc)
    db.commit()

    return ChatResponse(reply=reply, conversationId=conv.id)


@router.post("/chat/stream", summary="Send message and stream advisor reply")
async def post_chat_stream(
    payload: ChatRequestPayload,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Stream advisor reply as Server-Sent Events. Each event is data: {\"content\": \"...\"}; final event is data: {\"done\": true, \"conversationId\": id}."""
    message = (payload.message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    conversation_id = payload.conversationId
    conv = None
    if conversation_id:
        conv = _conversation_for_user(db, conversation_id, current_user.id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

    latest_eval = _latest_evaluation_summary(db, current_user.id)
    job_summary = None
    if payload.context and payload.context.jobId:
        try:
            from server.methods.FT_job_search import get_offer_by_id
            from server.routers.jobs_router import _flatten_offer
            offer_data = await asyncio.to_thread(get_offer_by_id, payload.context.jobId)
            flat = _flatten_offer(offer_data)
            job_summary = _job_offer_summary(flat)
        except ValueError as e:
            logger.warning("Could not load job offer (jobId=%s): %s", payload.context.jobId, e)

    intent = payload.context.intent if payload.context else None
    structured_cv = _latest_structured_cv(db, current_user.id) if intent == "cover_letter" else None
    system_prompt = _build_system_prompt(
        latest_eval, intent, job_summary, structured_cv=structured_cv
    )
    history = payload.conversationHistory or []
    history = history[-MAX_HISTORY_TURNS * 2 :]
    messages = [{"role": "system", "content": system_prompt}]
    for h in history:
        messages.append({"role": h.role, "content": h.content or ""})
    messages.append({"role": "user", "content": message})

    if not conv:
        conv = AdvisorConversation(
            user_id=current_user.id,
            title=DEFAULT_CONVERSATION_TITLE or None,
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)

    if not (conv.title or "").strip() and message:
        snippet = message[:TITLE_SNIPPET_LENGTH].strip()
        if snippet:
            conv.title = snippet + ("..." if len(message) > TITLE_SNIPPET_LENGTH else "")
    user_msg = AdvisorMessage(conversation_id=conv.id, role="user", content=message)
    db.add(user_msg)
    db.commit()

    conversation_id = conv.id

    async def sse_stream():
        reply_parts: list[str] = []
        try:
            async for chunk in stream_llm_messages_async(
                messages,
                temperature=0.7,
                max_tokens=2000,
            ):
                reply_parts.append(chunk)
                yield f"data: {json.dumps({'content': chunk})}\n\n"
        except ValueError as e:
            error_db = SessionLocal()
            try:
                error_content = f"Assistant failed to generate response: {str(e)}"
                error_msg = AdvisorMessage(conversation_id=conversation_id, role="assistant", content=error_content)
                error_db.add(error_msg)
                conv_for_update = error_db.get(AdvisorConversation, conversation_id)
                if conv_for_update:
                    conv_for_update.updated_at = datetime.now(timezone.utc)
                error_db.commit()
            except SQLAlchemyError:
                logger.exception(
                    "Failed to persist assistant error message",
                    extra={"conversation_id": conversation_id},
                )
                error_db.rollback()
            finally:
                error_db.close()
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            return
        reply = "".join(reply_parts)
        fresh_db = SessionLocal()
        try:
            assistant_msg = AdvisorMessage(conversation_id=conversation_id, role="assistant", content=reply)
            fresh_db.add(assistant_msg)
            conv_for_update = fresh_db.get(AdvisorConversation, conversation_id)
            if conv_for_update:
                conv_for_update.updated_at = datetime.now(timezone.utc)
            fresh_db.commit()
        except SQLAlchemyError:
            logger.exception(
                "DB persistence failed for assistant reply",
                extra={"conversation_id": conversation_id},
            )
            fresh_db.rollback()
            yield f"data: {json.dumps({'error': 'db persistence failed'})}\n\n"
            return
        finally:
            fresh_db.close()
        yield f"data: {json.dumps({'done': True, 'conversationId': conversation_id})}\n\n"

    return StreamingResponse(
        sse_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
