import React from "react";
import ReactMarkdown from "react-markdown";
import "../styles/job-detail.css";

// Full job offer interface matching backend columns
export interface JobOffer {
    id: string;
    intitule: string | null;
    description: string | null;
    dateCreation: string | null;
    dateActualisation: string | null;
    publieeDepuis?: number | null;
    romeCode: string | null;
    romeLibelle: string | null;
    appellationlibelle: string | null;
    typeContrat: string | null;
    typeContratLibelle: string | null;
    natureContrat: string | null;
    experienceExige: string | null;
    experienceLibelle: string | null;
    competences: unknown | null;
    dureeTravailLibelle: string | null;
    dureeTravailLibelleConverti: string | null;
    alternance: boolean | null;
    nombrePostes: number | null;
    accessibleTH: boolean | null;
    qualificationCode: string | null;
    qualificationLibelle: string | null;
    codeNAF: string | null;
    secteurActivite: string | null;
    secteurActiviteLibelle: string | null;
    offresManqueCandidats: boolean | null;
    entrepriseAdaptee: boolean | null;
    employeurHandiEngage: boolean | null;
    "lieuTravail_libelle": string | null;
    "lieuTravail_latitude": number | null;
    "lieuTravail_longitude": number | null;
    "lieuTravail_codePostal": string | null;
    "lieuTravail_commune": string | null;
    "entreprise_nom": string | null;
    "entreprise_entrepriseAdaptee": boolean | null;
    "salaire_libelle": string | null;
    "contact_nom": string | null;
    "contact_coordonnees1": string | null;
    "contact_courriel": string | null;
    "origineOffre_origine": string | null;
    "origineOffre_urlOrigine": string | null;
    "contexteTravail_horaires": string | null;
    formations: unknown | null;
    qualitesProfessionnelles: unknown | null;
    "salaire_complement1": string | null;
    "salaire_listeComplements": unknown | null;
    trancheEffectifEtab: string | null;
    experienceCommentaire: string | null;
    permis: unknown | null;
    "salaire_complement2": string | null;
    "contact_coordonnees2": string | null;
    "contact_coordonnees3": string | null;
    "agence_courriel": string | null;
    "salaire_commentaire": string | null;
    deplacementCode: string | null;
    deplacementLibelle: string | null;
    "entreprise_logo": string | null;
    "contact_urlPostulation": string | null;
    "contexteTravail_conditionsExercice": string | null;
    langues: unknown | null;
    "entreprise_description": string | null;
    "contact_telephone": string | null;
    "entreprise_url": string | null;
}

interface JobDetailProps {
    job: JobOffer;
    onClose: () => void;
}

const JobDetail: React.FC<JobDetailProps> = ({ job, onClose }) => {
    const formatDate = (dateString: string | null) => {
        if (!dateString) return 'N/A';
        try {
            return new Date(dateString).toLocaleDateString();
        } catch {
            return dateString;
        }
    };

    const formatExigence = (exigence: string | null | undefined) => {
        if (!exigence) return '';
        if (exigence === 'S') return 'Souhaitée';
        if (exigence === 'E') return 'Exigée';
        return exigence;
    };

    const normalizeArray = (value: unknown, fieldName?: string): any[] => {
        if (value === null || value === undefined) return [];
        if (Array.isArray(value)) return value;
        if (typeof value === "string") {
            try {
                const parsed = JSON.parse(value);
                return Array.isArray(parsed) ? parsed : [];
            } catch (error) {
                console.error(`normalizeArray: failed to parse JSON for ${fieldName ?? 'value'}`, error, value);
                return [];
            }
        }
        // Unexpected shape, log to surface backend contract issues.
        console.error(`normalizeArray: unexpected value for ${fieldName ?? 'value'}`, value);
        return [];
    };

    const renderField = (label: string, value: unknown) => {
        if (!value && value !== 0 && value !== false) return null;

        let displayValue: string;
        if (typeof value === 'boolean') {
            displayValue = value ? 'Oui' : 'Non';
        } else if (typeof value === 'object') {
            displayValue = JSON.stringify(value);
        } else {
            displayValue = String(value);
        }

        return (
            <div className="jd-field">
                <span className="jd-field-label">{label}:</span>
                <span>{displayValue}</span>
            </div>
        );
    };

    const renderContactValue = (value: string) => {
        if (!value) return null;
        const trimmed = value.trim();
        const isUrl = /^https?:\/\//i.test(trimmed);
        const isEmail = /@/.test(trimmed) && !isUrl;
        if (isUrl) {
            return (
                <a href={trimmed} target="_blank" rel="noopener noreferrer" className="nb-btn nb-btn--ghost" style={{ padding: '0.35rem 0.6rem', fontSize: '0.9rem' }}>
                    Ouvrir le lien
                </a>
            );
        }
        if (isEmail) {
            return (
                <a href={`mailto:${trimmed}`} className="nb-btn nb-btn--ghost" style={{ padding: '0.35rem 0.6rem', fontSize: '0.9rem' }}>
                    {trimmed}
                </a>
            );
        }
        return <span>{trimmed}</span>;
    };

    const normalizeUrl = (val: string | null | undefined) => {
        if (!val) return null;
        const trimmed = val.trim();
        return /^(https?:\/\/|mailto:)/i.test(trimmed) ? trimmed : null;
    };

    const applicationUrl = normalizeUrl(
        job["contact_urlPostulation"]
        || job["origineOffre_urlOrigine"]
        || job["entreprise_url"]
    );

    const isAppLink = (val: unknown) => {
        if (typeof val !== "string") return false;
        const trimmed = val.trim();
        return trimmed.includes('Pour postuler') || (applicationUrl && trimmed === applicationUrl);
    };
    const contactEmail = (job["contact_courriel"] || job["agence_courriel"]) && !isAppLink(job["contact_courriel"] || job["agence_courriel"]) ? (job["contact_courriel"] || job["agence_courriel"]) : null;
    const contactPhone = job["contact_telephone"] || job["contact_coordonnees1"];
    const locationLabel = job["lieuTravail_libelle"];
    const contractLabel = job.typeContratLibelle || job.typeContrat;
    const company = job["entreprise_nom"] || 'Entreprise non spécifiée';
    const competencesList = normalizeArray(job.competences, 'competences');
    const qualitesList = normalizeArray(job.qualitesProfessionnelles, 'qualitesProfessionnelles');
    const formationsList = normalizeArray(job.formations, 'formations');
    const horairesList = normalizeArray(job["contexteTravail_horaires"], 'contexteTravail_horaires');
    const salaireComplementsList = normalizeArray(job["salaire_listeComplements"], 'salaire_listeComplements');
    const permisList = normalizeArray(job.permis, 'permis');
    const lat = job["lieuTravail_latitude"];
    const lng = job["lieuTravail_longitude"];
    const hasCoords = typeof lat === 'number' && typeof lng === 'number' && Number.isFinite(lat) && Number.isFinite(lng) && !(lat === 0 && lng === 0);

    return (
        <div className="jd-overlay">
            <div className="jd-panel">
                <div className="jd-header">
                    <div className="jd-title-row">
                        <div style={{ flex: 1 }}>
                            <h2 className="jd-title">{job.intitule || 'Sans titre'}</h2>
                            <p className="jd-subtitle">{company}</p>
                            {locationLabel && (
                                <p className="jd-subtitle" style={{ opacity: 0.7, margin: '0 0 0 0' }}>📍 {locationLabel}</p>
                            )}

                            <div className="jd-badges">
                                {contractLabel && <span className="jd-badge">💼 {contractLabel}</span>}
                                {job.romeCode && <span className="jd-badge">ROME {job.romeCode}</span>}
                                {job.publieeDepuis !== null && job.publieeDepuis !== undefined && (
                                    <span className="jd-badge">Publié: {job.publieeDepuis} jours</span>
                                )}
                                {(job.dateActualisation || job.dateCreation) && (
                                    <span className="jd-badge">📅 {formatDate(job.dateActualisation || job.dateCreation)}</span>
                                )}
                                {job.alternance && <span className="jd-badge">Alternance</span>}
                            </div>
                        </div>

                        <div className="jd-actions">
                            {applicationUrl && (
                                <a
                                    className="nb-btn"
                                    href={applicationUrl}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                >
                                    Postuler
                                </a>
                            )}

                            {!applicationUrl && contactEmail && (
                                <a
                                    className="nb-btn"
                                    href={`mailto:${contactEmail}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                >
                                    Postuler par email
                                </a>
                            )}

                            {contactEmail && (
                                <a
                                    className="nb-btn nb-btn--secondary"
                                    href={`mailto:${contactEmail}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                >
                                    Contacter
                                </a>
                            )}

                            <button className="nb-btn nb-btn--ghost" onClick={onClose}>
                                Fermer
                            </button>
                        </div>
                    </div>
                </div>

                <div className="jd-body">
                    <div className="jd-section">
                        <h3>Description</h3>
                        {job.description ? (
                            <ReactMarkdown className="jd-markdown">{job.description}</ReactMarkdown>
                        ) : (
                            <p className="jd-subtitle">Aucune description fournie.</p>
                        )}
                    </div>

                    {(job["salaire_libelle"] || job["salaire_commentaire"] || job["salaire_complement1"] || job["salaire_complement2"] || salaireComplementsList.length > 0) && (
                        <div className="jd-section">
                            <h3>Rémunération</h3>
                            {renderField('Salaire', job["salaire_libelle"])}
                            {renderField('Commentaire', job["salaire_commentaire"])}
                            {salaireComplementsList.length > 0 ? (
                                <div style={{ marginTop: '0.4rem' }}>
                                    <div className="jd-field-label" style={{ marginBottom: '0.4rem' }}>Compléments</div>
                                    <div className="jd-meta-grid">
                                        {salaireComplementsList.map((item, idx) => {
                                            const it: any = item || {};
                                            return (
                                                <div key={idx} className="jd-chip" style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
                                                    <strong>{it.libelle || 'Complément'}</strong>
                                                    {it.code && <span style={{ fontSize: '0.85rem', opacity: 0.8 }}>Code: {it.code}</span>}
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            ) : (
                                <>
                                    {renderField('Complément 1', job["salaire_complement1"])}
                                    {renderField('Complément 2', job["salaire_complement2"])}
                                </>
                            )}
                        </div>
                    )}

                    {(contractLabel || job.natureContrat || job.dureeTravailLibelle || job.alternance || job.nombrePostes || job.deplacementLibelle || job.deplacementCode) && (
                        <div className="jd-section">
                            <h3>Détails du contrat</h3>
                            {renderField('Type de contrat', contractLabel)}
                            {renderField('Nature du contrat', job.natureContrat)}
                            {renderField('Durée de travail', job.dureeTravailLibelle)}
                            {renderField('Alternance', job.alternance)}
                            {renderField('Nombre de postes', job.nombrePostes)}
                            {renderField('Déplacement', job.deplacementLibelle || job.deplacementCode)}
                        </div>
                    )}

                    {(job["entreprise_nom"] || job.secteurActiviteLibelle || job.secteurActivite || job.codeNAF || job.trancheEffectifEtab || job["entreprise_entrepriseAdaptee"] || job.entrepriseAdaptee || job.employeurHandiEngage || job["entreprise_url"]) && (
                        <div className="jd-section">
                            <h3>Entreprise</h3>
                            {renderField('Nom', job["entreprise_nom"])}
                            {renderField("Secteur d'activité", job.secteurActiviteLibelle || job.secteurActivite)}
                            {renderField('Code NAF', job.codeNAF)}
                            {renderField('Tranche effectif', job.trancheEffectifEtab)}
                            {renderField('Entreprise adaptée', job["entreprise_entrepriseAdaptee"] ?? job.entrepriseAdaptee)}
                            {renderField('Employeur handi-engagé', job.employeurHandiEngage)}
                            {job["entreprise_url"] && (
                                <a
                                    className="nb-btn nb-btn--secondary"
                                    href={job["entreprise_url"]}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    style={{ marginTop: '0.5rem' }}
                                >
                                    Site web
                                </a>
                            )}
                        </div>
                    )}

                    {(job.experienceLibelle || job.experienceExige || job.experienceCommentaire || job.qualificationLibelle || job.qualificationCode || competencesList.length > 0 || formationsList.length > 0 || qualitesList.length > 0 || !!job.langues || permisList.length > 0) && (
                        <div className="jd-section">
                            <h3>Expérience et qualifications</h3>
                            {renderField('Expérience exigée', job.experienceLibelle || job.experienceExige)}
                            {renderField('Commentaire', job.experienceCommentaire)}
                            {renderField('Qualification', job.qualificationLibelle || job.qualificationCode)}
                            {competencesList.length > 0 && (
                                <div style={{ marginTop: '0.4rem' }}>
                                    <div className="jd-field-label" style={{ marginBottom: '0.4rem' }}>Compétences</div>
                                    <div className="jd-meta-grid">
                                        {competencesList.map((comp, idx) => {
                                            const c: any = comp || {};
                                            return (
                                                <div key={idx} className="jd-chip" style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
                                                    <strong>{c.libelle || 'Compétence'}</strong>
                                                    <span style={{ fontSize: '0.85rem', opacity: 0.8 }}>
                                                        {c.code ? `Code: ${c.code}` : ''}{c.code && c.exigence ? ' • ' : ''}{c.exigence ? formatExigence(c.exigence) : ''}
                                                    </span>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            )}
                            {formationsList.length > 0 && (
                                <div style={{ marginTop: '0.4rem' }}>
                                    <div className="jd-field-label" style={{ marginBottom: '0.4rem' }}>Formations</div>
                                    <div className="jd-meta-grid">
                                        {formationsList.map((f, idx) => {
                                            const form: any = f || {};
                                            return (
                                                <div key={idx} className="jd-chip" style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                                                    <strong>{form.domaineLibelle || 'Formation'}</strong>
                                                    {form.niveauLibelle && <span style={{ fontSize: '0.9rem', opacity: 0.85 }}>{form.niveauLibelle}</span>}
                                                    {form.commentaire && <span style={{ fontSize: '0.9rem', opacity: 0.85 }}>{form.commentaire}</span>}
                                                    {form.exigence && <span style={{ fontSize: '0.85rem', opacity: 0.8 }}>{formatExigence(form.exigence)}</span>}
                                                    {form.codeFormation && <span style={{ fontSize: '0.85rem', opacity: 0.8 }}>Code: {form.codeFormation}</span>}
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            )}
                            {qualitesList.length > 0 && (
                                <div style={{ marginTop: '0.4rem' }}>
                                    <div className="jd-field-label" style={{ marginBottom: '0.4rem' }}>Qualités professionnelles</div>
                                    <div className="jd-meta-grid">
                                        {qualitesList.map((q, idx) => {
                                            const qual: any = q || {};
                                            return (
                                                <div key={idx} className="jd-chip" style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                                                    <strong>{qual.libelle || 'Qualité'}</strong>
                                                    {qual.description && (
                                                        <span style={{ fontSize: '0.9rem', opacity: 0.85 }}>{qual.description}</span>
                                                    )}
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            )}
                            {permisList.length > 0 && (
                                <div style={{ marginTop: '0.4rem' }}>
                                    <div className="jd-field-label" style={{ marginBottom: '0.4rem' }}>Permis</div>
                                    <div className="jd-meta-grid">
                                        {permisList.map((p, idx) => {
                                            const perm: any = p || {};
                                            return (
                                                <div key={idx} className="jd-chip" style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
                                                    <strong>{perm.libelle || 'Permis'}</strong>
                                                    {perm.exigence && <span style={{ fontSize: '0.85rem', opacity: 0.8 }}>{formatExigence(perm.exigence)}</span>}
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            )}
                            {renderField('Langues', job.langues)}
                        </div>
                    )}

                    <div className="jd-section jd-section--map">
                        <h3>Lieu de travail{locationLabel ? ` — ${locationLabel}` : ''}</h3>
                        {hasCoords ? (
                            <iframe
                                width="100%"
                                style={{ border: 0, minHeight: '180px' }}
                                loading="lazy"
                                title={`Carte du lieu de travail${locationLabel ? ` — ${locationLabel}` : ''}`}
                                src={`https://www.openstreetmap.org/export/embed.html?bbox=${lng - 0.01},${lat - 0.01},${lng + 0.01},${lat + 0.01}&layer=mapnik&marker=${lat},${lng}`}
                            />
                        ) : (
                            <p className="jd-subtitle">Coordonnées non disponibles</p>
                        )}
                    </div>

                    {(horairesList.length > 0 || job["contexteTravail_conditionsExercice"]) && (
                        <div className="jd-section">
                            <h3>Contexte de travail</h3>
                            {horairesList.length > 0 && (
                                <div className="jd-field" style={{ display: 'block' }}>
                                    <span className="jd-field-label">Horaires :</span>
                                    <ul style={{ margin: '0.35rem 0 0 0', paddingLeft: '1.2rem', lineHeight: 1.6 }}>
                                        {horairesList.map((h, idx) => (
                                            <li key={idx}>{typeof h === 'string' ? h : JSON.stringify(h)}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                            {renderField("Conditions d'exercice", job["contexteTravail_conditionsExercice"])}
                        </div>
                    )}

                    {(job["contact_nom"] || (contactPhone && !isAppLink(contactPhone)) || (job["contact_coordonnees2"] && !isAppLink(job["contact_coordonnees2"])) || (job["contact_coordonnees3"] && !isAppLink(job["contact_coordonnees3"])) || (contactEmail && !isAppLink(contactEmail)) || (job["agence_courriel"] && !isAppLink(job["agence_courriel"]))) && (
                        <div className="jd-section">
                            <h3>Contact</h3>
                            {renderField('Nom', job["contact_nom"])}
                            {contactPhone && !isAppLink(contactPhone) && (
                                <div className="jd-field">
                                    <span className="jd-field-label">Téléphone :</span>{' '}
                                    {renderContactValue(contactPhone)}
                                </div>
                            )}
                            {job["contact_coordonnees1"] && !isAppLink(job["contact_coordonnees1"]) && job["contact_coordonnees1"] !== contactPhone && (
                                <div className="jd-field">
                                    <span className="jd-field-label">Adresse :</span>{' '}
                                    {renderContactValue(String(job["contact_coordonnees1"]))}
                                </div>
                            )}
                            {job["contact_coordonnees2"] && !isAppLink(job["contact_coordonnees2"]) && (
                                <div className="jd-field">
                                    <span className="jd-field-label">Adresse :</span>{' '}
                                    {renderContactValue(String(job["contact_coordonnees2"]))}
                                </div>
                            )}
                            {job["contact_coordonnees3"] && !isAppLink(job["contact_coordonnees3"]) && (
                                <div className="jd-field">
                                    <span className="jd-field-label">Adresse :</span>{' '}
                                    {renderContactValue(String(job["contact_coordonnees3"]))}
                                </div>
                            )}
                            {contactEmail && !isAppLink(contactEmail) && (
                                <div className="jd-field">
                                    <span className="jd-field-label">Email :</span>{' '}
                                    {renderContactValue(contactEmail)}
                                </div>
                            )}
                            {job["agence_courriel"] && !isAppLink(job["agence_courriel"]) && (
                                <div className="jd-field">
                                    <span className="jd-field-label">Email agence :</span>{' '}
                                    {renderContactValue(String(job["agence_courriel"]))}
                                </div>
                            )}
                        </div>
                    )}

                    {(job.dateCreation || job.dateActualisation || job.accessibleTH || job.offresManqueCandidats || job["origineOffre_origine"] || job["origineOffre_urlOrigine"]) && (
                        <div className="jd-section">
                            <h3>Informations complémentaires</h3>
                            {renderField('Date de création', formatDate(job.dateCreation))}
                            {renderField("Date d'actualisation", formatDate(job.dateActualisation))}
                            {renderField('Accessible TH', job.accessibleTH)}
                            {renderField('Offres manque candidats', job.offresManqueCandidats)}
                            {renderField("Origine de l'offre", job["origineOffre_origine"])}
                            {job["origineOffre_urlOrigine"] && (
                                <a
                                    className="nb-btn nb-btn--ghost"
                                    href={job["origineOffre_urlOrigine"]}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    style={{ marginTop: '0.5rem' }}
                                >
                                    Voir l'offre d'origine
                                </a>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default JobDetail;
