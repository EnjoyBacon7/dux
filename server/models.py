from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, LargeBinary, Boolean, Text
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=True)  # Nullable for passkey-only users
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # Profile information
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    title = Column(String, nullable=True)
    profile_picture = Column(String, nullable=True)  # URL or path to profile picture
    linkedin_id = Column(String, nullable=True, unique=True)  # LinkedIn user ID for OAuth tracking

    # Extended profile fields
    email = Column(String, nullable=True)
    headline = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    linkedin_profile_url = Column(String, nullable=True)
    cv_filename = Column(String, nullable=True)  # Stored CV filename
    skills = Column(ARRAY(String), nullable=True)  # Array of skills

    # Setup tracking
    profile_setup_completed = Column(Boolean, default=False)

    # Account security
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    passkey_credentials = relationship("PasskeyCredential", back_populates="user", cascade="all, delete-orphan")
    webauthn_challenges = relationship("WebAuthnChallenge", back_populates="user", cascade="all, delete-orphan")
    login_attempts = relationship("LoginAttempt", back_populates="user", cascade="all, delete-orphan")
    experiences = relationship("Experience", back_populates="user", cascade="all, delete-orphan")
    educations = relationship("Education", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class PasskeyCredential(Base):
    __tablename__ = "passkey_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    credential_id = Column(String, unique=True, nullable=False, index=True)
    public_key = Column(LargeBinary, nullable=False)
    sign_count = Column(Integer, default=0)
    transports = Column(String, nullable=True)  # JSON string of transport methods
    aaguid = Column(String, nullable=True)  # Authenticator AAGUID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship
    user = relationship("User", back_populates="passkey_credentials")

    def __repr__(self):
        return f"<PasskeyCredential(id={self.id}, user_id={self.user_id}, credential_id={self.credential_id[:16]}...)>"


class WebAuthnChallenge(Base):
    __tablename__ = "webauthn_challenges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for pre-registration
    username = Column(String, nullable=True, index=True)  # For pre-registration challenges
    challenge = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Relationship
    user = relationship("User", back_populates="webauthn_challenges")

    def __repr__(self):
        return f"<WebAuthnChallenge(id={self.id}, user_id={self.user_id})>"


class LoginAttempt(Base):
    __tablename__ = "login_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    success = Column(Boolean, nullable=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    attempted_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    user = relationship("User", back_populates="login_attempts")

    def __repr__(self):
        return f"<LoginAttempt(id={self.id}, user_id={self.user_id}, success={self.success})>"


class Experience(Base):
    __tablename__ = "experiences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company = Column(String, nullable=False)
    title = Column(String, nullable=False)
    start_date = Column(String, nullable=True)  # Stored as YYYY-MM format
    end_date = Column(String, nullable=True)  # Stored as YYYY-MM format
    is_current = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    user = relationship("User", back_populates="experiences")

    def __repr__(self):
        return f"<Experience(id={self.id}, user_id={self.user_id}, company={self.company}, title={self.title})>"


class Education(Base):
    __tablename__ = "educations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    school = Column(String, nullable=False)
    degree = Column(String, nullable=False)
    field_of_study = Column(String, nullable=True)
    start_date = Column(String, nullable=True)  # Stored as YYYY-MM format
    end_date = Column(String, nullable=True)  # Stored as YYYY-MM format
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    user = relationship("User", back_populates="educations")

    def __repr__(self):
        return f"<Education(id={self.id}, user_id={self.user_id}, school={self.school}, degree={self.degree})>"
