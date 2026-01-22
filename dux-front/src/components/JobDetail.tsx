import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import "../styles/job-detail.css";
import { useLanguage } from "../contexts/useLanguage";
import JobMatchAnalysis from "./JobMatchAnalysis";
import type { JobOffer } from "../types/job";

// Re-export types for backward compatibility
export type { JobOffer, OptimalOffer } from "../types/job";

interface JobDetailProps {
    job: JobOffer;
    onClose: () => void;
}

//  Helper pour ne sélectionner que les champs pertinents et non-sensibles
const pickAnalysisFields = (job: JobOffer): JobOffer => {
    // On crée un objet partiel ne contenant que les données métier utiles pour l'IA
    // et on exclut explicitement toutes les données de contact (PII)
    const safeJob: Partial<JobOffer> = {
        id: job.id,
        intitule: job.intitule,
        description: job.description,
        entreprise_nom: job.entreprise_nom,
        competences: job.competences,
        formations: job.formations,
        qualitesProfessionnelles: job.qualitesProfessionnelles,
        experienceLibelle: job.experienceLibelle,
        experienceExige: job.experienceExige,
        qualificationLibelle: job.qualificationLibelle,
        qualificationCode: job.qualificationCode,
        romeCode: job.romeCode,
        romeLibelle: job.romeLibelle,
        secteurActivite: job.secteurActivite,
        secteurActiviteLibelle: job.secteurActiviteLibelle,
        typeContrat: job.typeContrat,
        typeContratLibelle: job.typeContratLibelle,
        lieuTravail_libelle: job.lieuTravail_libelle
    };

    // On le cast en JobOffer pour satisfaire TypeScript (les champs manquants seront undefined)
    return safeJob as JobOffer;
};

const JobDetail: React.FC<JobDetailProps> = ({ job, onClose }) => {
    const { t } = useLanguage(); // Utilisation du hook de traduction
    const [showAnalysis, setShowAnalysis] = useState(false);

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

    return (
        <div className="jd-overlay">
            <div className="jd-panel">
                <div className="jd-header">
                    <div className="jd-title-row">
                        <div style={{ flex: 1 }}>
                            <h2 className="jd-title">{job.intitule || 'Sans titre'}</h2>
                            <p className="jd-subtitle">{job["entreprise_nom"] || 'Entreprise non spécifiée'}</p>
                            {job["lieuTravail_libelle"] && (
                                <p className="jd-subtitle" style={{ opacity: 0.7, margin: '0 0 0 0' }}>📍 {job["lieuTravail_libelle"]}</p>
                            )}

                            <div className="jd-badges">
                                {(job.typeContratLibelle || job.typeContrat) && <span className="jd-badge">💼 {job.typeContratLibelle || job.typeContrat}</span>}
                                {job.romeCode && <span className="jd-badge">ROME {job.romeCode}</span>}
                            </div>

                            <div style={{ marginTop: '1rem' }}>
                                <button
                                    onClick={() => setShowAnalysis(true)}
                                    className="nb-btn"
                                    style={{
                                        backgroundColor: 'var(--nb-accent)',
                                        color: 'var(--nb-fg)',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '0.5rem',
                                        padding: '0.5rem 1rem'
                                    }}
                                >
                                    <span>⚡</span> {t('analyze_match_ai')}
                                </button>
                            </div>
                        </div>

                        <div className="jd-actions">
                            {job["contact_urlPostulation"] && (
                                <a
                                    className="nb-btn"
                                    href={job["contact_urlPostulation"]}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                >
                                    Postuler
                                </a>
                            )}

                            <button className="nb-btn nb-btn--ghost" onClick={onClose}>
                                Fermer
                            </button>
                        </div>
                    </div>
                </div>

                <div className="jd-body">
                    {job.description && (
                        <div className="jd-section">
                            <h3>Description</h3>
                            <ReactMarkdown className="jd-markdown">{job.description}</ReactMarkdown>
                        </div>
                    )}

                    {(job.typeContratLibelle || job.typeContrat || job.natureContrat || job.dureeTravailLibelle) && (
                        <div className="jd-section">
                            <h3>Détails du contrat</h3>
                            {renderField('Type de contrat', job.typeContratLibelle || job.typeContrat)}
                            {renderField('Nature du contrat', job.natureContrat)}
                            {renderField('Durée de travail', job.dureeTravailLibelle)}
                            {renderField('Alternance', job.alternance)}
                            {renderField('Nombre de postes', job.nombrePostes)}
                        </div>
                    )}

                    {(job.experienceLibelle || job.experienceExige || job.qualificationLibelle || normalizeArray(job.competences).length > 0 || normalizeArray(job.formations).length > 0) && (
                        <div className="jd-section">
                            <h3>Expérience et qualifications</h3>
                            {renderField('Expérience exigée', job.experienceLibelle || job.experienceExige)}
                            {renderField('Commentaire', job.experienceCommentaire)}
                            {renderField('Qualification', job.qualificationLibelle || job.qualificationCode)}
                            {normalizeArray(job.competences, 'competences').length > 0 && (
                                <div style={{ marginTop: '0.4rem' }}>
                                    <div className="jd-field-label" style={{ marginBottom: '0.4rem' }}>Compétences</div>
                                    <div className="jd-meta-grid">
                                        {normalizeArray(job.competences).map((comp, idx) => {
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
                        </div>
                    )}

                    {(job["salaire_libelle"] || job["salaire_commentaire"] || job["salaire_complement1"]) && (
                        <div className="jd-section">
                            <h3>Rémunération</h3>
                            {renderField('Salaire', job["salaire_libelle"])}
                            {renderField('Commentaire', job["salaire_commentaire"])}
                            {renderField('Complément 1', job["salaire_complement1"])}
                            {renderField('Complément 2', job["salaire_complement2"])}
                        </div>
                    )}

                    {(job["entreprise_nom"] || job.secteurActiviteLibelle || job.codeNAF) && (
                        <div className="jd-section">
                            <h3>Entreprise</h3>
                            {renderField('Nom', job["entreprise_nom"])}
                            {renderField('Secteur d\'activité', job.secteurActiviteLibelle || job.secteurActivite)}
                            {renderField('Code NAF', job.codeNAF)}
                            {renderField('Tranche effectif', job.trancheEffectifEtab)}
                            {renderField('Entreprise adaptée', job["entreprise_entrepriseAdaptee"] || job.entrepriseAdaptee)}
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

                    {(job["lieuTravail_libelle"] || job["lieuTravail_commune"] || job.deplacementLibelle) && (
                        <div className="jd-section">
                            <h3>Lieu de travail</h3>
                            {renderField('Lieu', job["lieuTravail_libelle"])}
                            {renderField('Commune', job["lieuTravail_commune"])}
                            {renderField('Code postal', job["lieuTravail_codePostal"])}
                            {renderField('Déplacement', job.deplacementLibelle || job.deplacementCode)}

                            {/* OpenStreetMap embed when coordinates are available */}
                            {job["lieuTravail_latitude"] && job["lieuTravail_longitude"] && (() => {
                                const lat = parseFloat(job["lieuTravail_latitude"]);
                                const lon = parseFloat(job["lieuTravail_longitude"]);
                                return !isNaN(lat) && !isNaN(lon) && (
                                    <div className="jd-map-container" style={{ marginTop: '1rem' }}>
                                        <iframe
                                            title="Job Location Map"
                                            width="100%"
                                            height="250"
                                            style={{ border: '1px solid var(--nb-fg)', borderRadius: '6px' }}
                                            src={`https://www.openstreetmap.org/export/embed.html?bbox=${lon - 0.01}%2C${lat - 0.01}%2C${lon + 0.01}%2C${lat + 0.01}&layer=mapnik&marker=${lat}%2C${lon}`}
                                        />
                                        <a
                                            href={`https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=15/${lat}/${lon}`}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            style={{
                                                display: 'inline-block',
                                                marginTop: '0.5rem',
                                                fontSize: '0.85rem',
                                                opacity: 0.7
                                            }}
                                        >
                                            Voir sur OpenStreetMap ↗
                                        </a>
                                    </div>
                                );
                            })()}
                        </div>
                    )}

                    {(job["contact_courriel"] || job["contact_telephone"]) && (
                        <div className="jd-section">
                            <h3>Contact</h3>
                            {renderField('Nom', job["contact_nom"])}
                            {renderField('Téléphone', job["contact_telephone"] || job["contact_coordonnees1"])}
                            {renderField('Email', job["contact_courriel"])}
                        </div>
                    )}

                    {(job.romeCode || job.dateCreation) && (
                        <div className="jd-section">
                            <h3>Informations complémentaires</h3>
                            {renderField('Code ROME', job.romeCode)}
                            {renderField('Libellé ROME', job.romeLibelle)}
                            {renderField('Date de création', formatDate(job.dateCreation))}
                            {renderField('Date d\'actualisation', formatDate(job.dateActualisation))}
                            {renderField('Accessible TH', job.accessibleTH)}
                        </div>
                    )}
                </div>
            </div>

            {showAnalysis && (
                <JobMatchAnalysis
                    job={pickAnalysisFields(job)}
                    onClose={() => setShowAnalysis(false)}
                />
            )}
        </div>
    );
};

export default JobDetail;