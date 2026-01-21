import React, { useState } from "react";
import { useLanguage } from "../contexts/useLanguage"; //  hook de traduction
import JobMatchAnalysis from "./JobMatchAnalysis";

// Full job offer interface 
export interface JobOffer {
    id: string;
    intitule: string | null;
    description: string | null;
    dateCreation: string | null;
    dateActualisation: string | null;
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

    const renderSection = (title: string, content: React.ReactNode) => {
        if (!content) return null;
        return (
            <div style={{ marginBottom: '1.5rem' }}>
                <h3 style={{
                    margin: '0 0 0.75rem 0',
                    fontSize: '1.125rem',
                    fontWeight: 600,
                    opacity: 0.9
                }}>
                    {title}
                </h3>
                <div style={{ lineHeight: 1.6 }}>
                    {content}
                </div>
            </div>
        );
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
            <div style={{ marginBottom: '0.5rem', display: 'flex', gap: '0.5rem' }}>
                <span style={{ fontWeight: 600, minWidth: '140px' }}>{label}:</span>
                <span>{displayValue}</span>
            </div>
        );
    };

    return (
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '2rem'
        }}>
            <div style={{
                backgroundColor: 'var(--nb-bg)',
                border: 'var(--nb-border) solid var(--nb-fg)',
                borderRadius: '8px',
                maxWidth: '900px',
                width: '100%',
                maxHeight: '90vh',
                overflowY: 'auto',
                padding: '2rem',
                boxShadow: '8px 8px 0 var(--nb-fg)'
            }}>
                {/* Header */}
                <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    marginBottom: '1.5rem',
                    paddingBottom: '1rem',
                    borderBottom: 'var(--nb-border) solid var(--nb-fg)'
                }}>
                    <div style={{ flex: 1 }}>
                        <h2 style={{ margin: '0 0 0.5rem 0', fontSize: '1.75rem' }}>
                            {job.intitule || 'Sans titre'}
                        </h2>
                        <div style={{ fontSize: '1.125rem', opacity: 0.8 }}>
                            {job["entreprise_nom"] || 'Entreprise non spécifiée'}
                        </div>
                        {job["lieuTravail_libelle"] && (
                            <div style={{ marginTop: '0.5rem', opacity: 0.7 }}>
                                📍 {job["lieuTravail_libelle"]}
                            </div>
                        )}
                        
                        {/* --- BUTTON: AI MATCH ANALYSIS --- */}
                        <div style={{ marginTop: '1rem' }}>
                            <button
                                onClick={() => setShowAnalysis(true)}
                                className="nb-btn"
                                style={{ 
                                    backgroundColor: 'var(--nb-accent)', 
                                    color: 'white',
                                    display: 'flex', 
                                    alignItems: 'center', 
                                    gap: '0.5rem',
                                    padding: '0.5rem 1rem'
                                }}
                            >
                                <span>⚡</span> {t('analyze_match_ai')}
                            </button>
                        </div>
                        {/* ------------------------------------- */}

                    </div>
                    <button
                        onClick={onClose}
                        className="nb-btn-secondary"
                        style={{ minWidth: '100px' }}
                    >
                        Fermer
                    </button>
                </div>

                {/* Description */}
                {renderSection('Description', job.description && (
                    <div style={{ whiteSpace: 'pre-wrap' }}>{job.description}</div>
                ))}

                {/* Contract Details */}
                {renderSection('Détails du contrat', (
                    <>
                        {renderField('Type de contrat', job.typeContratLibelle || job.typeContrat)}
                        {renderField('Nature du contrat', job.natureContrat)}
                        {renderField('Durée de travail', job.dureeTravailLibelle)}
                        {renderField('Alternance', job.alternance)}
                        {renderField('Nombre de postes', job.nombrePostes)}
                    </>
                ))}

                {/* Experience & Qualifications */}
                {renderSection('Expérience et qualifications', (
                    <>
                        {renderField('Expérience exigée', job.experienceLibelle || job.experienceExige)}
                        {job.experienceCommentaire && renderField('Commentaire', job.experienceCommentaire)}
                        {renderField('Qualification', job.qualificationLibelle || job.qualificationCode)}
                        {job.competences && renderField('Compétences', JSON.stringify(job.competences))}
                        {job.formations && renderField('Formations', JSON.stringify(job.formations))}
                        {job.qualitesProfessionnelles && renderField('Qualités professionnelles', JSON.stringify(job.qualitesProfessionnelles))}
                        {job.langues && renderField('Langues', JSON.stringify(job.langues))}
                        {job.permis && renderField('Permis', JSON.stringify(job.permis))}
                    </>
                ))}

                {/* Salary */}
                {(job["salaire_libelle"] || job["salaire_complement1"] || job["salaire_complement2"]) &&
                    renderSection('Rémunération', (
                        <>
                            {renderField('Salaire', job["salaire_libelle"])}
                            {renderField('Complément 1', job["salaire_complement1"])}
                            {renderField('Complément 2', job["salaire_complement2"])}
                            {job["salaire_commentaire"] && renderField('Commentaire', job["salaire_commentaire"])}
                            {job["salaire_listeComplements"] && renderField('Liste compléments', job["salaire_listeComplements"])}
                        </>
                    ))
                }

                {/* Company Info */}
                {renderSection('Entreprise', (
                    <>
                        {renderField('Nom', job["entreprise_nom"])}
                        {job["entreprise_description"] && renderField('Description', job["entreprise_description"])}
                        {renderField('Secteur d\'activité', job.secteurActiviteLibelle || job.secteurActivite)}
                        {renderField('Code NAF', job.codeNAF)}
                        {renderField('Tranche effectif', job.trancheEffectifEtab)}
                        {renderField('Entreprise adaptée', job["entreprise_entrepriseAdaptee"] || job.entrepriseAdaptee)}
                        {renderField('Employeur handi-engagé', job.employeurHandiEngage)}
                        {job["entreprise_url"] && (
                            <div style={{ marginTop: '0.5rem' }}>
                                <a href={job["entreprise_url"]} target="_blank" rel="noopener noreferrer" className="nb-btn-secondary">
                                    Site web de l'entreprise
                                </a>
                            </div>
                        )}
                    </>
                ))}

                {/* Location Details */}
                {renderSection('Lieu de travail', (
                    <>
                        {renderField('Libellé', job["lieuTravail_libelle"])}
                        {renderField('Commune', job["lieuTravail_commune"])}
                        {renderField('Code postal', job["lieuTravail_codePostal"])}
                        {job["lieuTravail_latitude"] && job["lieuTravail_longitude"] &&
                            renderField('Coordonnées', `${job["lieuTravail_latitude"]}, ${job["lieuTravail_longitude"]}`)}
                        {renderField('Déplacement', job.deplacementLibelle || job.deplacementCode)}
                    </>
                ))}

                {/* Work Context */}
                {(job["contexteTravail_horaires"] || job["contexteTravail_conditionsExercice"]) &&
                    renderSection('Contexte de travail', (
                        <>
                            {job["contexteTravail_horaires"] && renderField('Horaires', job["contexteTravail_horaires"])}
                            {job["contexteTravail_conditionsExercice"] && renderField('Conditions d\'exercice', job["contexteTravail_conditionsExercice"])}
                        </>
                    ))
                }

                {/* Contact Information */}
                {renderSection('Contact', (
                    <>
                        {renderField('Nom', job["contact_nom"])}
                        {renderField('Téléphone', job["contact_telephone"] || job["contact_coordonnees1"])}
                        {renderField('Coordonnées 2', job["contact_coordonnees2"])}
                        {renderField('Coordonnées 3', job["contact_coordonnees3"])}
                        {renderField('Email', job["contact_courriel"])}
                        {renderField('Email agence', job["agence_courriel"])}
                        {job["contact_urlPostulation"] && (
                            <div style={{ marginTop: '0.75rem' }}>
                                <a href={job["contact_urlPostulation"]} target="_blank" rel="noopener noreferrer" className="nb-btn">
                                    Postuler
                                </a>
                            </div>
                        )}
                    </>
                ))}

                {/* Additional Info */}
                {renderSection('Informations complémentaires', (
                    <>
                        {renderField('Code ROME', job.romeCode)}
                        {renderField('Libellé ROME', job.romeLibelle)}
                        {renderField('Appellation', job.appellationlibelle)}
                        {renderField('Date de création', formatDate(job.dateCreation))}
                        {renderField('Date d\'actualisation', formatDate(job.dateActualisation))}
                        {renderField('Accessible TH', job.accessibleTH)}
                        {renderField('Offres manque candidats', job.offresManqueCandidats)}
                        {job["origineOffre_origine"] && renderField('Origine de l\'offre', job["origineOffre_origine"])}
                        {job["origineOffre_urlOrigine"] && (
                            <div style={{ marginTop: '0.5rem' }}>
                                <a href={job["origineOffre_urlOrigine"]} target="_blank" rel="noopener noreferrer" className="nb-btn-secondary">
                                    Voir l'offre d'origine
                                </a>
                            </div>
                        )}
                    </>
                ))}
            </div>

            {/* Render the Analysis Modal when showAnalysis is true */}
            {showAnalysis && (
                <JobMatchAnalysis 
                    job={pickAnalysisFields(job)} // <--- On envoie la version "nettoyée" ici !
                    onClose={() => setShowAnalysis(false)} 
                />
            )}
        </div>
    );
};

export default JobDetail;