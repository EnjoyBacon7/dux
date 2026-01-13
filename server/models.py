from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, LargeBinary, Boolean, Text
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY, JSON

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
    cv_text = Column(Text, nullable=True)  # Extracted text from CV
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


class Offres_FT(Base):
    __tablename__ = "offres_FT"

    id = Column(String, primary_key=True)
    intitule = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    dateCreation = Column(DateTime, nullable=False)
    dateActualisation = Column(DateTime, nullable=False)
    romeCode = Column(String, nullable=True)
    romeLibelle = Column(String, nullable=True)
    appellationlibelle = Column(String, nullable=True)
    typeContrat = Column(String, nullable=True)
    typeContratLibelle = Column(String, nullable=True)
    natureContrat = Column(String, nullable=True)
    experienceExige = Column(String, nullable=True)
    experienceLibelle = Column(String, nullable=True)
    competences = Column(ARRAY(Text), nullable=True)
    dureeTravailLibelle = Column(String, nullable=True)
    dureeTravailLibelleConverti = Column(String, nullable=True)
    alternance = Column(Boolean, nullable=True)
    nombrePostes = Column(Integer, nullable=True)
    accessibleTH = Column(Boolean, nullable=True)
    qualificationCode = Column(String, nullable=True)
    qualificationLibelle = Column(String, nullable=True)
    codeNAF = Column(String, nullable=True)
    secteurActivite = Column(String, nullable=True)
    secteurActiviteLibelle = Column(String, nullable=True)
    offresManqueCandidats = Column(Boolean, nullable=True)
    entrepriseAdaptee = Column(Boolean, nullable=True)
    employeurHandiEngage = Column(Boolean, nullable=True)
    lieuTravail_libelle = Column(String, nullable=True)
    lieuTravail_latitude = Column(String, nullable=True)
    lieuTravail_longitude = Column(String, nullable=True)
    lieuTravail_codePostal = Column(String, nullable=True)
    lieuTravail_commune = Column(String, nullable=True)
    entreprise_nom = Column(String, nullable=True)
    entreprise_entrepriseAdaptee = Column(Boolean, nullable=True)
    salaire_libelle = Column(String, nullable=True)
    contact_nom = Column(String, nullable=True)
    contact_coordonnees1 = Column(String, nullable=True)
    contact_courriel = Column(String, nullable=True)
    origineOffre_origine = Column(String, nullable=True)
    origineOffre_urlOrigine = Column(String, nullable=True)
    contexteTravail_horaires = Column(String, nullable=True)
    formations = Column(ARRAY(Text), nullable=True)
    qualitesProfessionnelles = Column(ARRAY(Text), nullable=True)
    salaire_complement1 = Column(String, nullable=True)
    salaire_listeComplements = Column(ARRAY(Text), nullable=True)
    trancheEffectifEtab = Column(String, nullable=True)
    experienceCommentaire = Column(Text, nullable=True)
    permis = Column(ARRAY(Text), nullable=True)
    salaire_complement2 = Column(String, nullable=True)
    contact_coordonnees2 = Column(String, nullable=True)
    contact_coordonnees3 = Column(String, nullable=True)
    agence_courriel = Column(String, nullable=True)
    salaire_commentaire = Column(Text, nullable=True)
    deplacementCode = Column(String, nullable=True)
    deplacementLibelle = Column(String, nullable=True)
    entreprise_logo = Column(String, nullable=True)
    contact_urlPostulation = Column(String, nullable=True)
    contexteTravail_conditionsExercice = Column(Text, nullable=True)
    langues = Column(ARRAY(Text), nullable=True)
    entreprise_description = Column(Text, nullable=True)
    contact_telephone = Column(String, nullable=True)
    entreprise_url = Column(String, nullable=True)

    def __repr__(self):
        return f"<Offres_FT(id={self.id})>"
    

class Fiche_Metier_ROME(Base):
    __tablename__ = "fiche_metier_rome"
    
    code = Column(String, unique=True, nullable=False, index=True, primary_key=True)
    metier = Column(JSON, nullable=False)  # {code, libelle}
    groupesCompetencesMobilisees = Column(JSON, nullable=False)  # Array of competency groups
    groupesSavoirs = Column(JSON, nullable=False)  # Array of knowledge groups

    def __repr__(self):
        return f"<Fiche_Metier_ROME(code={self.code})>"
