import React, { useState, useEffect } from "react";
import Header from "./components/Header";
import JobDetail from "./components/JobDetail";
import type { JobOffer } from "./components/JobDetail";
import { useLanguage } from "./contexts/useLanguage";

const JobSearch: React.FC = () => {
    const { t } = useLanguage();
    const [searchQuery, setSearchQuery] = useState('');
    const [jobs, setJobs] = useState<JobOffer[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [selectedJob, setSelectedJob] = useState<JobOffer | null>(null);
    const [page, setPage] = useState(1);
    const [total, setTotal] = useState(0);
    const pageSize = 20;

    // Fetch jobs from API
    useEffect(() => {
        const fetchJobs = async () => {
            setLoading(true);
            setError(null);
            try {
                const params = new URLSearchParams({
                    page: page.toString(),
                    page_size: pageSize.toString(),
                });
                if (searchQuery) {
                    params.append('q', searchQuery);
                }

                const response = await fetch(`/api/jobs/search?${params}`);
                if (!response.ok) {
                    throw new Error('Failed to fetch jobs');
                }

                const data = await response.json();
                setJobs(data.results || []);
                setTotal(data.total || 0);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'An error occurred');
                setJobs([]);
            } finally {
                setLoading(false);
            }
        };

        fetchJobs();
    }, [searchQuery, page]);

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

    const handleSearch = (value: string) => {
        setSearchQuery(value);
        setPage(1); // Reset to first page on new search
    };

    const handleNextPage = () => {
        if (page * pageSize < total) {
            setPage(page + 1);
        }
    };

    const handlePreviousPage = () => {
        if (page > 1) {
            setPage(page - 1);
        }
    };

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
                gridTemplateColumns: '320px 1fr',
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
                        {/* Search Input */}
                        <div>
                            <label style={{
                                display: 'block',
                                marginBottom: '0.5rem',
                                fontSize: '0.875rem',
                                fontWeight: 600,
                                opacity: 0.8
                            }}>
                                Recherche
                            </label>
                            <input
                                type="text"
                                className="nb-input"
                                placeholder={t('jobs.search_placeholder')}
                                value={searchQuery}
                                onChange={(e) => handleSearch(e.target.value)}
                                style={{ width: '100%' }}
                            />
                        </div>

                        {/* Clear Search Button */}
                        {searchQuery && (
                            <div>
                                <button
                                    onClick={() => handleSearch('')}
                                    className="nb-btn-secondary"
                                    style={{ fontSize: '0.875rem', width: '100%' }}
                                >
                                    Effacer la recherche
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

                        {/* Pagination Info */}
                        {!loading && total > 0 && (
                            <div style={{
                                padding: '0.5rem',
                                textAlign: 'center',
                                fontSize: '0.75rem',
                                opacity: 0.7
                            }}>
                                Page {page} sur {Math.ceil(total / pageSize)}
                            </div>
                        )}
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

                                {/* Pagination Controls */}
                                {total > pageSize && (
                                    <div style={{
                                        display: 'flex',
                                        justifyContent: 'center',
                                        gap: '1rem',
                                        marginTop: '2rem',
                                        paddingBottom: '2rem'
                                    }}>
                                        <button
                                            onClick={handlePreviousPage}
                                            disabled={page === 1}
                                            className="nb-btn-secondary"
                                            style={{
                                                opacity: page === 1 ? 0.5 : 1,
                                                cursor: page === 1 ? 'not-allowed' : 'pointer'
                                            }}
                                        >
                                            ← Précédent
                                        </button>
                                        <span style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            padding: '0 1rem',
                                            fontWeight: 600
                                        }}>
                                            Page {page} / {Math.ceil(total / pageSize)}
                                        </span>
                                        <button
                                            onClick={handleNextPage}
                                            disabled={page * pageSize >= total}
                                            className="nb-btn-secondary"
                                            style={{
                                                opacity: page * pageSize >= total ? 0.5 : 1,
                                                cursor: page * pageSize >= total ? 'not-allowed' : 'pointer'
                                            }}
                                        >
                                            Suivant →
                                        </button>
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default JobSearch;
