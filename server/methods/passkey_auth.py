from fastapi import HTTPException, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone
import base64
from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
    options_to_json,
)
from webauthn.helpers.structs import (
    PublicKeyCredentialDescriptor,
    UserVerificationRequirement,
    AuthenticatorSelectionCriteria,
    ResidentKeyRequirement,
    AuthenticatorAttachment,
)
from webauthn.helpers.cose import COSEAlgorithmIdentifier

from server.database import get_db_session
from server.models import User, PasskeyCredential, WebAuthnChallenge
from server.config import settings
from server.validators import validate_username


# Configuration from settings
RP_ID = settings.rp_id
RP_NAME = settings.rp_name
ORIGIN = settings.origin
CHALLENGE_TIMEOUT_MINUTES = settings.challenge_timeout_minutes


class PasskeyRegisterOptionsRequest(BaseModel):
    username: str


class PasskeyRegisterVerifyRequest(BaseModel):
    username: str
    credential: Dict[str, Any]


class PasskeyLoginOptionsRequest(BaseModel):
    username: str


class PasskeyLoginVerifyRequest(BaseModel):
    username: str
    credential: Dict[str, Any]


def cleanup_expired_challenges(db: Session):
    """Remove expired challenges from the database"""
    now = datetime.now(timezone.utc)
    db.query(WebAuthnChallenge).filter(WebAuthnChallenge.expires_at < now).delete()
    db.commit()


async def get_passkey_register_options(request: PasskeyRegisterOptionsRequest, db: Session = Depends(get_db_session)):
    """
    Generate WebAuthn registration options for a new passkey
    """
    username = request.username.strip() if request.username else ""

    # Validate username
    is_valid, error_msg = validate_username(username)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    cleanup_expired_challenges(db)

    # Check if user exists
    user = db.query(User).filter(User.username == username).first()

    # Get existing credentials to exclude them (only if user exists)
    exclude_credentials: List[PublicKeyCredentialDescriptor] = []
    if user:
        existing_credentials = db.query(PasskeyCredential).filter(
            PasskeyCredential.user_id == user.id
        ).all()
        exclude_credentials = [
            PublicKeyCredentialDescriptor(id=bytes.fromhex(cred.credential_id))
            for cred in existing_credentials
        ]

    # Generate user_id for registration (use actual user.id if exists, otherwise hash username)
    import hashlib
    user_id_for_options = user.id if user else int(hashlib.sha256(username.encode()).hexdigest()[:8], 16)

    # Generate registration options
    options = generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_id=str(user_id_for_options).encode('utf-8'),
        user_name=username,
        user_display_name=username,
        exclude_credentials=exclude_credentials,
        authenticator_selection=AuthenticatorSelectionCriteria(
            authenticator_attachment=AuthenticatorAttachment.PLATFORM,
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
        supported_pub_key_algs=[
            COSEAlgorithmIdentifier.ECDSA_SHA_256,
            COSEAlgorithmIdentifier.RSASSA_PKCS1_v1_5_SHA_256,
        ],
    )

    # Store challenge in database
    challenge = WebAuthnChallenge(
        user_id=user.id if user else None,
        username=username if not user else None,
        challenge=base64.urlsafe_b64encode(options.challenge).decode('ascii'),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=CHALLENGE_TIMEOUT_MINUTES)
    )
    db.add(challenge)
    db.commit()

    return options_to_json(options)


async def verify_passkey_registration(request: PasskeyRegisterVerifyRequest, db: Session = Depends(get_db_session)):
    """
    Verify and store a new passkey credential
    """
    username = request.username.strip() if request.username else ""
    credential = request.credential

    # Validate username
    is_valid, error_msg = validate_username(username)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # Check if user exists
    user = db.query(User).filter(User.username == username).first()

    # Get the most recent challenge
    if user:
        challenge_record = db.query(WebAuthnChallenge).filter(
            WebAuthnChallenge.user_id == user.id
        ).order_by(WebAuthnChallenge.created_at.desc()).first()
    else:
        challenge_record = db.query(WebAuthnChallenge).filter(
            WebAuthnChallenge.username == username
        ).order_by(WebAuthnChallenge.created_at.desc()).first()

    if not challenge_record:
        raise HTTPException(status_code=400, detail="No challenge found")

    if challenge_record.expires_at < datetime.now(timezone.utc):
        db.delete(challenge_record)
        db.commit()
        raise HTTPException(status_code=400, detail="Challenge expired")

    # Verify the registration response
    verification = verify_registration_response(
        credential=credential,
        expected_challenge=base64.urlsafe_b64decode(challenge_record.challenge),
        expected_rp_id=RP_ID,
        expected_origin=ORIGIN,
    )

    # Create user if they don't exist (only after successful verification)
    if not user:
        user = User(username=username)
        db.add(user)
        db.flush()

    # Normalize credential_id as hex string
    credential_id_hex = verification.credential_id.hex() if isinstance(
        verification.credential_id, (bytes, bytearray)) else str(
        verification.credential_id)

    # Prevent duplicate registration
    if db.query(PasskeyCredential).filter(PasskeyCredential.credential_id == credential_id_hex).first():
        raise HTTPException(status_code=409, detail="This passkey is already registered")

    # Store credential
    aaguid_value = verification.aaguid if hasattr(verification, 'aaguid') else None
    aaguid_str = aaguid_value.hex() if isinstance(
        aaguid_value, (bytes, bytearray)) else (
        str(aaguid_value) if aaguid_value else None)

    passkey_cred = PasskeyCredential(
        user_id=user.id,
        credential_id=credential_id_hex,
        public_key=verification.credential_public_key,
        sign_count=verification.sign_count,
        aaguid=aaguid_str,
    )
    db.add(passkey_cred)
    db.delete(challenge_record)
    db.commit()

    return {
        "success": True,
        "message": "Passkey registered successfully",
        "verified": True
    }


async def get_passkey_login_options(request: PasskeyLoginOptionsRequest, db: Session = Depends(get_db_session)):
    """
    Generate WebAuthn authentication options for passkey login
    """
    username = request.username.strip() if request.username else ""

    # Validate username
    is_valid, error_msg = validate_username(username)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    cleanup_expired_challenges(db)

    # Check if user exists
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get user's credentials
    user_credentials = db.query(PasskeyCredential).filter(
        PasskeyCredential.user_id == user.id
    ).all()

    if not user_credentials:
        raise HTTPException(status_code=404, detail="No passkeys found for this user")

    # Convert credentials to format needed by py_webauthn
    allow_credentials: List[PublicKeyCredentialDescriptor] = [
        PublicKeyCredentialDescriptor(id=bytes.fromhex(cred.credential_id))
        for cred in user_credentials
    ]

    # Generate authentication options
    options = generate_authentication_options(
        rp_id=RP_ID,
        allow_credentials=allow_credentials,
        user_verification=UserVerificationRequirement.PREFERRED,
    )

    # Store challenge
    challenge = WebAuthnChallenge(
        user_id=user.id,
        challenge=base64.urlsafe_b64encode(options.challenge).decode('ascii'),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=CHALLENGE_TIMEOUT_MINUTES)
    )
    db.add(challenge)
    db.commit()

    return options_to_json(options)


async def verify_passkey_login(request: PasskeyLoginVerifyRequest, req: Request, db: Session = Depends(get_db_session)):
    """
    Verify a passkey authentication attempt
    """
    username = request.username.strip() if request.username else ""
    credential = request.credential

    # Validate username
    is_valid, error_msg = validate_username(username)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # Verify user exists
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get the most recent challenge
    challenge_record = db.query(WebAuthnChallenge).filter(
        WebAuthnChallenge.user_id == user.id
    ).order_by(WebAuthnChallenge.created_at.desc()).first()

    if not challenge_record:
        raise HTTPException(status_code=400, detail="No challenge found")

    if challenge_record.expires_at < datetime.now(timezone.utc):
        db.delete(challenge_record)
        db.commit()
        raise HTTPException(status_code=400, detail="Challenge expired")

    # Get credential from database
    credential_id_b64url = credential.get("rawId") or credential.get("id")
    if not credential_id_b64url:
        raise HTTPException(status_code=400, detail="Missing credential id")

    # Convert base64url id to hex to match stored format
    import base64 as _b64
    b64 = credential_id_b64url.replace('-', '+').replace('_', '/')
    pad = len(b64) % 4
    if pad:
        b64 += '=' * (4 - pad)

    try:
        cred_id_bytes = _b64.b64decode(b64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid credential id encoding")

    credential_id_hex = cred_id_bytes.hex()

    passkey_cred = db.query(PasskeyCredential).filter(
        PasskeyCredential.user_id == user.id,
        PasskeyCredential.credential_id == credential_id_hex
    ).first()

    if not passkey_cred:
        raise HTTPException(status_code=401, detail="Invalid credential")

    # Verify the authentication response
    verification = verify_authentication_response(
        credential=credential,
        expected_challenge=base64.urlsafe_b64decode(challenge_record.challenge),
        expected_rp_id=RP_ID,
        expected_origin=ORIGIN,
        credential_public_key=passkey_cred.public_key,
        credential_current_sign_count=passkey_cred.sign_count,
    )

    # Update credential
    passkey_cred.sign_count = verification.new_sign_count
    passkey_cred.last_used_at = datetime.now(timezone.utc)
    db.delete(challenge_record)
    db.commit()

    # Regenerate session
    req.session.clear()
    req.session["user_id"] = user.id
    req.session["username"] = user.username
    req.session["authenticated_at"] = datetime.now(timezone.utc).isoformat()

    return {
        "success": True,
        "message": "Authentication successful",
        "username": username,
        "verified": True
    }
