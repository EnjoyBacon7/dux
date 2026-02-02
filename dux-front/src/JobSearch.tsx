import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import Header from "./components/Header";
import JobDetail from "./components/JobDetail";
import OfferBox from "./components/OfferBox";
import type { JobOffer } from "./types/job";
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
    const [searchParams] = useSearchParams();
    const [filters, setFilters] = useState<FTSearchFilters>(() => {
        const romeFromQuery = searchParams.get("codeROME") || searchParams.get("rome");
        return romeFromQuery ? { codeROME: romeFromQuery } : {};
    });
    const [jobs, setJobs] = useState<JobOffer[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [selectedJob, setSelectedJob] = useState<JobOffer | null>(null);
    const [total, setTotal] = useState(0);

    useEffect(() => {
        const romeFromQuery = searchParams.get("codeROME") || searchParams.get("rome");
        if (!romeFromQuery) return;
        setFilters(prev => (
            prev.codeROME === romeFromQuery ? prev : { ...prev, codeROME: romeFromQuery }
        ));
    }, [searchParams]);

    // Open a specific job by ID from URL (e.g. /jobs?open=JOB_ID) – used by Tracker "View job"
    useEffect(() => {
        const openId = searchParams.get("open");
        if (!openId || !openId.trim()) return;
        const controller = new AbortController();
        const fetchAndOpen = async () => {
            try {
                const res = await fetch(`/api/jobs/offer/${encodeURIComponent(openId.trim())}`, {
                    credentials: "include",
                    signal: controller.signal,
                });
                if (!res.ok) return;
                const data = await res.json();
                const offer = data?.offer;
                if (offer && typeof offer.id === "string") {
                    setSelectedJob(offer as JobOffer);
                }
            } catch (err) {
                if (err instanceof Error && err.name !== "AbortError") {
                    console.error(`Error fetching job ${openId}:`, err);
                }
            }
        };
        fetchAndOpen();
        return () => controller.abort();
    }, [searchParams]);

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
                                {t('jobs.keywords')}
                            </label>
                            <input
                                type="text"
                                className="nb-input"
                                placeholder={t('jobs.keywords_placeholder')}
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
                                {t('jobs.location')}
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
                                        {t('jobs.commune')}
                                    </label>
                                    <input
                                        type="text"
                                        className="nb-input"
                                        placeholder={t('jobs.commune_placeholder')}
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
                                        {t('jobs.department')}
                                    </label>
                                    <input
                                        type="text"
                                        className="nb-input"
                                        placeholder={t('jobs.department_placeholder')}
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
                                        {t('jobs.region')}
                                    </label>
                                    <input
                                        type="text"
                                        className="nb-input"
                                        placeholder={t('jobs.region_placeholder')}
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
                                        {t('jobs.distance')}
                                    </label>
                                    <input
                                        type="number"
                                        className="nb-input"
                                        placeholder={t('jobs.distance_placeholder')}
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
                                {t('jobs.contract_type')}
                            </label>
                            <select
                                className="nb-input"
                                value={filters.typeContrat || ''}
                                onChange={(e) => updateFilter('typeContrat', e.target.value)}
                                style={{ width: '100%' }}
                            >
                                <option value="">{t('jobs.all_types')}</option>
                                <option value="CDI">{t('jobs.contract_cdi')}</option>
                                <option value="CDD">{t('jobs.contract_cdd')}</option>
                                <option value="MIS">{t('jobs.contract_mis')}</option>
                                <option value="SAI">{t('jobs.contract_sai')}</option>
                                <option value="LIB">{t('jobs.contract_lib')}</option>
                                <option value="REP">{t('jobs.contract_rep')}</option>
                                <option value="FRA">{t('jobs.contract_fra')}</option>
                                <option value="CCE">{t('jobs.contract_cce')}</option>
                                <option value="CPE">{t('jobs.contract_cpe')}</option>
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
                                {t('jobs.experience_level')}
                            </label>
                            <select
                                className="nb-input"
                                value={filters.experienceExigence || ''}
                                onChange={(e) => updateFilter('experienceExigence', e.target.value)}
                                style={{ width: '100%' }}
                            >
                                <option value="">{t('jobs.all_levels')}</option>
                                <option value="D">{t('jobs.experience_beginner')}</option>
                                <option value="S">{t('jobs.experience_1_3')}</option>
                                <option value="E">{t('jobs.experience_3_plus')}</option>
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
                                {t('jobs.qualification')}
                            </label>
                            <select
                                className="nb-input"
                                value={filters.qualification || ''}
                                onChange={(e) => updateFilter('qualification', e.target.value)}
                                style={{ width: '100%' }}
                            >
                                <option value="">{t('jobs.all')}</option>
                                <option value="0">{t('jobs.non_executive')}</option>
                                <option value="9">{t('jobs.executive')}</option>
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
                                {t('jobs.time_type')}
                            </label>
                            <select
                                className="nb-input"
                                value={filters.tempsPlein === undefined ? '' : filters.tempsPlein.toString()}
                                onChange={(e) => updateFilter('tempsPlein', e.target.value === '' ? undefined : e.target.value === 'true')}
                                style={{ width: '100%' }}
                            >
                                <option value="">{t('jobs.all')}</option>
                                <option value="true">{t('jobs.type_fulltime')}</option>
                                <option value="false">{t('jobs.type_parttime')}</option>
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
                                {t('jobs.min_salary')}
                            </label>
                            <input
                                type="number"
                                className="nb-input"
                                placeholder={t('jobs.min_salary_placeholder')}
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
                                {t('jobs.published_since')}
                            </label>
                            <select
                                className="nb-input"
                                value={filters.publieeDepuis || ''}
                                onChange={(e) => updateFilter('publieeDepuis', e.target.value ? Number(e.target.value) : undefined)}
                                style={{ width: '100%' }}
                            >
                                <option value="">{t('jobs.all_dates')}</option>
                                <option value="1">{t('jobs.today')}</option>
                                <option value="3">{t('jobs.last_3_days')}</option>
                                <option value="7">{t('jobs.last_7_days')}</option>
                                <option value="14">{t('jobs.last_14_days')}</option>
                                <option value="30">{t('jobs.last_30_days')}</option>
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
                                {t('jobs.rome_code')}
                            </label>
                            <input
                                type="text"
                                className="nb-input"
                                placeholder={t('jobs.rome_code_placeholder')}
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
                                {t('jobs.sector')}
                            </label>
                            <input
                                type="text"
                                className="nb-input"
                                placeholder={t('jobs.sector_placeholder')}
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
                                    {t('jobs.reset_filters')}
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
                            {loading ? t('jobs.loading') : `${total} ${total > 1 ? t('jobs.offers_found_plural') : t('jobs.offers_found_singular')}`}
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
                                    {t('jobs.loading_offers')}
                                </p>
                            </div>
                        ) : error ? (
                            <div className="nb-card" style={{ textAlign: 'center', padding: '3rem 1rem' }}>
                                <p style={{ fontSize: '1.125rem', margin: 0, opacity: 0.7, color: 'red' }}>
                                    {t('jobs.error')}: {error}
                                </p>
                            </div>
                        ) : jobs.length === 0 ? (
                            <div className="nb-card" style={{ textAlign: 'center', padding: '3rem 1rem' }}>
                                <p style={{ fontSize: '1.125rem', margin: 0, opacity: 0.7 }}>
                                    {t('jobs.no_offers_found')}
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
                                        <OfferBox
                                            title={job.intitule || t('jobs.untitled')}
                                            company={job["entreprise_nom"] ?? undefined}
                                            location={job["lieuTravail_libelle"] ?? undefined}
                                            contractType={job.typeContratLibelle ?? undefined}
                                            date={job.dateActualisation || job.dateCreation || undefined}
                                            description={job.description ?? undefined}
                                            salary={job["salaire_libelle"] ?? undefined}
                                            onViewDetails={(e?: any) => {
                                                if (e && e.stopPropagation) e.stopPropagation();
                                                setSelectedJob(job);
                                            }}
                                        />
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
