import React, { useState, useEffect } from "react";
import Header from "./components/Header";
import JobDetail from "./components/JobDetail";
import type { JobOffer } from "./components/JobDetail";
import { useLanguage } from "./contexts/useLanguage";

interface FTSearchFilters {
    motsCles?: string;
    codeROME?: string;
    commune?: string;
    departement?: string;
    region?: string;
    distance?: number;
    typeContrat?: string;
    natureContrat?: string;
    experienceExigence?: string;
    qualification?: string;
    tempsPlein?: boolean;
    salaireMin?: string;
    publieeDepuis?: number;
    secteurActivite?: string;
}

const JobSearch: React.FC = () => {
    const { t } = useLanguage();
    const [filters, setFilters] = useState<FTSearchFilters>({});
    const [jobs, setJobs] = useState<JobOffer[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [selectedJob, setSelectedJob] = useState<JobOffer | null>(null);
    const [total, setTotal] = useState(0);

    // Fetch jobs from France Travail API
    useEffect(() => {
        const fetchJobs = async () => {
            setLoading(true);
            setError(null);
            try {
                const params = new URLSearchParams();

                // Add all non-empty filter parameters
                Object.entries(filters).forEach(([key, value]) => {
                    if (value !== undefined && value !== null && value !== '') {
                        params.append(key, String(value));
                    }
                });

                // Always sort by relevance (0 = relevance, 1 = date, 2 = distance)
                // Override any user-selected sort value to ensure relevance sorting
                params.set('sort', '0');

                const response = await fetch(`/api/jobs/load_offers?${params}`, {
                    method: 'POST'
                });
                if (!response.ok) {
                    throw new Error('Failed to fetch jobs');
                }

                const data = await response.json();
                // load_offers returns the array directly
                const jobsArray = Array.isArray(data) ? data : [];
                setJobs(jobsArray);
                setTotal(jobsArray.length);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'An error occurred');
                setJobs([]);
            } finally {
                setLoading(false);
            }
        };

        fetchJobs();
    }, [filters]);

    const formatDate = (dateString: string | null) => {
        if (!dateString) return 'N/A';
        try {
            const date = new Date(dateString);
            const now = new Date();
            const diffTime = Math.abs(now.getTime() - date.getTime());
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

            if (diffDays === 1) return t('jobs.posted_today');
            if (diffDays < 7) return t('jobs.posted_days_ago').replace('{days}', diffDays.toString());
            if (diffDays < 30) {
                const weeks = Math.floor(diffDays / 7);
                return t('jobs.posted_weeks_ago').replace('{weeks}', weeks.toString());
            }
            return date.toLocaleDateString();
        } catch {
            return dateString;
        }
    };

    const updateFilter = (key: keyof FTSearchFilters, value: any) => {
        setFilters(prev => ({
            ...prev,
            [key]: value === '' ? undefined : value
        }));
    };

    const clearFilters = () => {
        setFilters({});
    };

    const hasActiveFilters = Object.values(filters).some(v => v !== undefined && v !== null && v !== '');

    return (
        <div style={{
            width: '100%',
            margin: 0,
            padding: 0,
            minHeight: '100vh',
            backgroundColor: 'var(--nb-bg)'
        }}>
            <Header />
            <div style={{
                display: 'grid',
                gridTemplateColumns: '400px 1fr',
                gap: 0,
                minHeight: 'calc(100vh - 60px)',
                width: '100%',
                maxWidth: '100%',
                backgroundColor: 'var(--nb-bg)'
            }}>
                {/* Left Sidebar - Filters */}
                <div style={{
                    padding: '1.5rem',
                    borderRight: 'var(--nb-border) solid var(--nb-fg)',
                    backgroundColor: 'var(--nb-bg)',
                    position: 'sticky',
                    top: '60px',
                    height: 'calc(100vh - 60px)',
                    overflowY: 'auto'
                }}>
                    <h2 style={{ margin: '0 0 1.5rem 0', fontSize: '1.25rem' }}>
                        {t('jobs.title')}
                    </h2>

                    {/* Search and Filters */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        {/* Keywords */}
                        <div>
                            <label style={{
                                display: 'block',
                                marginBottom: '0.5rem',
                                fontSize: '0.875rem',
                                fontWeight: 600,
                                opacity: 0.8
                            }}>
                                Mots-clés
                            </label>
                            <input
                                type="text"
                                className="nb-input"
                                placeholder="Ex: Développeur, Chef de projet..."
                                value={filters.motsCles || ''}
                                onChange={(e) => updateFilter('motsCles', e.target.value)}
                                style={{ width: '100%' }}
                            />
                        </div>

                        {/* Location Section */}
                        <div style={{
                            padding: '1rem',
                            border: 'var(--nb-border) solid var(--nb-fg)',
                            borderRadius: '6px'
                        }}>
                            <h3 style={{ margin: '0 0 1rem 0', fontSize: '1rem', fontWeight: 600 }}>
                                Localisation
                            </h3>

                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                {/* Commune (INSEE Code) */}
                                <div>
                                    <label style={{
                                        display: 'block',
                                        marginBottom: '0.5rem',
                                        fontSize: '0.875rem',
                                        fontWeight: 600,
                                        opacity: 0.8
                                    }}>
                                        Commune (Code INSEE)
                                    </label>
                                    <input
                                        type="text"
                                        className="nb-input"
                                        placeholder="Ex: 75056"
                                        value={filters.commune || ''}
                                        onChange={(e) => updateFilter('commune', e.target.value)}
                                        style={{ width: '100%' }}
                                    />
                                </div>

                                {/* Département */}
                                <div>
                                    <label style={{
                                        display: 'block',
                                        marginBottom: '0.5rem',
                                        fontSize: '0.875rem',
                                        fontWeight: 600,
                                        opacity: 0.8
                                    }}>
                                        Département
                                    </label>
                                    <input
                                        type="text"
                                        className="nb-input"
                                        placeholder="Ex: 75"
                                        value={filters.departement || ''}
                                        onChange={(e) => updateFilter('departement', e.target.value)}
                                        style={{ width: '100%' }}
                                    />
                                </div>

                                {/* Région */}
                                <div>
                                    <label style={{
                                        display: 'block',
                                        marginBottom: '0.5rem',
                                        fontSize: '0.875rem',
                                        fontWeight: 600,
                                        opacity: 0.8
                                    }}>
                                        Région
                                    </label>
                                    <input
                                        type="text"
                                        className="nb-input"
                                        placeholder="Ex: Île-de-France"
                                        value={filters.region || ''}
                                        onChange={(e) => updateFilter('region', e.target.value)}
                                        style={{ width: '100%' }}
                                    />
                                </div>

                                {/* Distance */}
                                <div>
                                    <label style={{
                                        display: 'block',
                                        marginBottom: '0.5rem',
                                        fontSize: '0.875rem',
                                        fontWeight: 600,
                                        opacity: 0.8
                                    }}>
                                        Distance (km)
                                    </label>
                                    <input
                                        type="number"
                                        className="nb-input"
                                        placeholder="Ex: 10"
                                        value={filters.distance || ''}
                                        onChange={(e) => updateFilter('distance', e.target.value ? Number(e.target.value) : undefined)}
                                        style={{ width: '100%' }}
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Contract Type */}
                        <div>
                            <label style={{
                                display: 'block',
                                marginBottom: '0.5rem',
                                fontSize: '0.875rem',
                                fontWeight: 600,
                                opacity: 0.8
                            }}>
                                Type de contrat
                            </label>
                            <select
                                className="nb-input"
                                value={filters.typeContrat || ''}
                                onChange={(e) => updateFilter('typeContrat', e.target.value)}
                                style={{ width: '100%' }}
                            >
                                <option value="">Tous les types</option>
                                <option value="CDI">CDI</option>
                                <option value="CDD">CDD</option>
                                <option value="MIS">MIS (Mission intérimaire)</option>
                                <option value="SAI">SAI (Saisonnier)</option>
                                <option value="LIB">LIB (Libéral)</option>
                                <option value="REP">REP (Reprise/Succession)</option>
                                <option value="FRA">FRA (Franchise)</option>
                                <option value="CCE">CCE (Contrat de chantier)</option>
                                <option value="CPE">CPE (Contrat de professionnalisation)</option>
                            </select>
                        </div>

                        {/* Experience Level */}
                        <div>
                            <label style={{
                                display: 'block',
                                marginBottom: '0.5rem',
                                fontSize: '0.875rem',
                                fontWeight: 600,
                                opacity: 0.8
                            }}>
                                Niveau d'expérience
                            </label>
                            <select
                                className="nb-input"
                                value={filters.experienceExigence || ''}
                                onChange={(e) => updateFilter('experienceExigence', e.target.value)}
                                style={{ width: '100%' }}
                            >
                                <option value="">Tous niveaux</option>
                                <option value="D">Débutant accepté</option>
                                <option value="S">1 à 3 ans</option>
                                <option value="E">3 ans et plus</option>
                            </select>
                        </div>

                        {/* Qualification */}
                        <div>
                            <label style={{
                                display: 'block',
                                marginBottom: '0.5rem',
                                fontSize: '0.875rem',
                                fontWeight: 600,
                                opacity: 0.8
                            }}>
                                Qualification
                            </label>
                            <select
                                className="nb-input"
                                value={filters.qualification || ''}
                                onChange={(e) => updateFilter('qualification', e.target.value)}
                                style={{ width: '100%' }}
                            >
                                <option value="">Tous</option>
                                <option value="0">Non cadre</option>
                                <option value="9">Cadre</option>
                            </select>
                        </div>

                        {/* Full/Part Time */}
                        <div>
                            <label style={{
                                display: 'block',
                                marginBottom: '0.5rem',
                                fontSize: '0.875rem',
                                fontWeight: 600,
                                opacity: 0.8
                            }}>
                                Temps plein / partiel
                            </label>
                            <select
                                className="nb-input"
                                value={filters.tempsPlein === undefined ? '' : filters.tempsPlein.toString()}
                                onChange={(e) => updateFilter('tempsPlein', e.target.value === '' ? undefined : e.target.value === 'true')}
                                style={{ width: '100%' }}
                            >
                                <option value="">Tous</option>
                                <option value="true">Temps plein</option>
                                <option value="false">Temps partiel</option>
                            </select>
                        </div>

                        {/* Minimum Salary */}
                        <div>
                            <label style={{
                                display: 'block',
                                marginBottom: '0.5rem',
                                fontSize: '0.875rem',
                                fontWeight: 600,
                                opacity: 0.8
                            }}>
                                Salaire minimum (€)
                            </label>
                            <input
                                type="number"
                                className="nb-input"
                                placeholder="Ex: 30000"
                                value={filters.salaireMin || ''}
                                onChange={(e) => updateFilter('salaireMin', e.target.value)}
                                style={{ width: '100%' }}
                            />
                        </div>

                        {/* Published Since */}
                        <div>
                            <label style={{
                                display: 'block',
                                marginBottom: '0.5rem',
                                fontSize: '0.875rem',
                                fontWeight: 600,
                                opacity: 0.8
                            }}>
                                Publiée depuis
                            </label>
                            <select
                                className="nb-input"
                                value={filters.publieeDepuis || ''}
                                onChange={(e) => updateFilter('publieeDepuis', e.target.value ? Number(e.target.value) : undefined)}
                                style={{ width: '100%' }}
                            >
                                <option value="">Toutes les dates</option>
                                <option value="1">Aujourd'hui</option>
                                <option value="3">3 derniers jours</option>
                                <option value="7">7 derniers jours</option>
                                <option value="14">14 derniers jours</option>
                                <option value="30">30 derniers jours</option>
                            </select>
                        </div>

                        {/* ROME Code */}
                        <div>
                            <label style={{
                                display: 'block',
                                marginBottom: '0.5rem',
                                fontSize: '0.875rem',
                                fontWeight: 600,
                                opacity: 0.8
                            }}>
                                Code ROME
                            </label>
                            <input
                                type="text"
                                className="nb-input"
                                placeholder="Ex: M1805"
                                value={filters.codeROME || ''}
                                onChange={(e) => updateFilter('codeROME', e.target.value)}
                                style={{ width: '100%' }}
                            />
                        </div>

                        {/* Sector */}
                        <div>
                            <label style={{
                                display: 'block',
                                marginBottom: '0.5rem',
                                fontSize: '0.875rem',
                                fontWeight: 600,
                                opacity: 0.8
                            }}>
                                Secteur d'activité
                            </label>
                            <input
                                type="text"
                                className="nb-input"
                                placeholder="Ex: Informatique"
                                value={filters.secteurActivite || ''}
                                onChange={(e) => updateFilter('secteurActivite', e.target.value)}
                                style={{ width: '100%' }}
                            />
                        </div>

                        {/* Clear Filters Button */}
                        {hasActiveFilters && (
                            <div>
                                <button
                                    onClick={clearFilters}
                                    className="nb-btn-secondary"
                                    style={{ fontSize: '0.875rem', width: '100%' }}
                                >
                                    Réinitialiser les filtres
                                </button>
                            </div>
                        )}

                        {/* Results Count */}
                        <div style={{
                            marginTop: '1rem',
                            padding: '0.75rem',
                            backgroundColor: 'var(--nb-accent)',
                            border: 'var(--nb-border) solid var(--nb-fg)',
                            borderRadius: '6px',
                            textAlign: 'center',
                            fontSize: '0.875rem',
                            fontWeight: 600
                        }}>
                            {loading ? 'Chargement...' : `${total} offre${total > 1 ? 's' : ''} trouvée${total > 1 ? 's' : ''}`}
                        </div>
                    </div>
                </div>

                {/* Right Side - Job Listings */}
                <div style={{
                    padding: '1.5rem',
                    overflowY: 'auto',
                    height: 'calc(100vh - 60px)'
                }}>
                    {selectedJob && (
                        <JobDetail job={selectedJob} onClose={() => setSelectedJob(null)} />
                    )}

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxWidth: '1200px' }}>
                        {loading ? (
                            <div className="nb-card" style={{ textAlign: 'center', padding: '3rem 1rem' }}>
                                <p style={{ fontSize: '1.125rem', margin: 0, opacity: 0.7 }}>
                                    Chargement des offres...
                                </p>
                            </div>
                        ) : error ? (
                            <div className="nb-card" style={{ textAlign: 'center', padding: '3rem 1rem' }}>
                                <p style={{ fontSize: '1.125rem', margin: 0, opacity: 0.7, color: 'red' }}>
                                    Erreur: {error}
                                </p>
                            </div>
                        ) : jobs.length === 0 ? (
                            <div className="nb-card" style={{ textAlign: 'center', padding: '3rem 1rem' }}>
                                <p style={{ fontSize: '1.125rem', margin: 0, opacity: 0.7 }}>
                                    Aucune offre trouvée
                                </p>
                            </div>
                        ) : (
                            <>
                                {jobs.map(job => (
                                    <div
                                        key={job.id}
                                        className="nb-card"
                                        style={{ cursor: 'pointer' }}
                                        onClick={() => setSelectedJob(job)}
                                    >
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                            {/* Job Header */}
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem' }}>
                                                <div style={{ flex: 1 }}>
                                                    <h3 style={{ margin: '0 0 0.25rem 0', fontSize: '1.25rem' }}>
                                                        {job.intitule || 'Sans titre'}
                                                    </h3>
                                                    <p style={{ margin: 0, fontSize: '1rem', opacity: 0.8 }}>
                                                        {job["entreprise_nom"] || 'Entreprise non spécifiée'}
                                                    </p>
                                                </div>
                                                {job["salaire_libelle"] && (
                                                    <div style={{
                                                        fontWeight: 600,
                                                        color: 'var(--nb-accent)',
                                                        textAlign: 'right',
                                                        fontSize: '1rem'
                                                    }}>
                                                        {job["salaire_libelle"]}
                                                    </div>
                                                )}
                                            </div>

                                            {/* Job Meta Info */}
                                            <div style={{
                                                display: 'flex',
                                                flexWrap: 'wrap',
                                                gap: '0.75rem',
                                                fontSize: '0.875rem',
                                                opacity: 0.7
                                            }}>
                                                {job["lieuTravail_libelle"] && (
                                                    <>
                                                        <span>📍 {job["lieuTravail_libelle"]}</span>
                                                        <span>•</span>
                                                    </>
                                                )}
                                                {job.typeContratLibelle && (
                                                    <>
                                                        <span>💼 {job.typeContratLibelle}</span>
                                                        <span>•</span>
                                                    </>
                                                )}
                                                <span>📅 {formatDate(job.dateActualisation || job.dateCreation)}</span>
                                            </div>

                                            {/* Job Description Preview */}
                                            {job.description && (
                                                <p style={{ margin: 0, lineHeight: 1.6 }}>
                                                    {job.description.length > 200
                                                        ? job.description.substring(0, 200) + '...'
                                                        : job.description}
                                                </p>
                                            )}

                                            {/* View Details Button */}
                                            <div style={{ marginTop: '0.5rem' }}>
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        setSelectedJob(job);
                                                    }}
                                                    className="nb-btn"
                                                >
                                                    Voir les détails
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default JobSearch;
