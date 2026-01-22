/**
 * Shared job offer types used across the application.
 * This ensures consistency between JobSearch, OptimalOffers, and JobDetail components.
 */

/**
 * Full job offer interface from France Travail API.
 * This is the complete data structure for a job offer.
 */
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

/**
 * Match metadata from the AI-powered profile matching.
 * Contains scoring and reasoning for why a job matches a user's profile.
 */
export interface JobMatchMetadata {
    position: number;
    score: number;
    match_reasons: string[];
    concerns?: string[];
    job_id?: string; // France Travail offer ID for fetching full data
}

/**
 * Optimal offer combines the full job offer with match metadata.
 * Used for displaying AI-matched job offers in the optimal offers carousel.
 */
export interface OptimalOffer extends JobOffer, JobMatchMetadata {}

/**
 * Helper to check if a job offer has match metadata (is an OptimalOffer).
 */
export function hasMatchMetadata(job: JobOffer | OptimalOffer): job is OptimalOffer {
    return 'score' in job && 'match_reasons' in job;
}
