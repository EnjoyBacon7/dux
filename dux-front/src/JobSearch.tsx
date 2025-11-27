import React, { useState, useMemo } from "react";
import Header from "./components/Header";
import { useLanguage } from "./contexts/useLanguage";

// Job interface - ready for backend integration
interface Job {
    id: string;
    title: string;
    company: string;
    location: string;
    type: 'full-time' | 'part-time' | 'contract' | 'internship';
    remote: boolean;
    salary?: {
        min: number;
        max: number;
        currency: string;
    };
    description: string;
    requirements: string[];
    posted: Date;
    applicationUrl?: string;
}

// Mock data - to be replaced with API calls
const MOCK_JOBS: Job[] = [
    {
        id: '1',
        title: 'Senior Software Engineer',
        company: 'TechCorp Inc.',
        location: 'San Francisco, CA',
        type: 'full-time',
        remote: true,
        salary: { min: 120000, max: 180000, currency: 'USD' },
        description: 'We are looking for a senior software engineer to join our team...',
        requirements: ['5+ years experience', 'React', 'TypeScript', 'Node.js'],
        posted: new Date('2024-11-20'),
        applicationUrl: 'https://example.com/apply'
    },
    {
        id: '2',
        title: 'Frontend Developer',
        company: 'Design Studio',
        location: 'New York, NY',
        type: 'full-time',
        remote: false,
        salary: { min: 80000, max: 120000, currency: 'USD' },
        description: 'Join our creative team to build beautiful user interfaces...',
        requirements: ['3+ years experience', 'React', 'CSS', 'UI/UX design'],
        posted: new Date('2024-11-22'),
        applicationUrl: 'https://example.com/apply'
    },
    {
        id: '3',
        title: 'Full Stack Developer',
        company: 'StartUp Labs',
        location: 'Remote',
        type: 'contract',
        remote: true,
        description: 'Help us build the next generation of web applications...',
        requirements: ['React', 'Python', 'PostgreSQL', 'AWS'],
        posted: new Date('2024-11-25'),
        applicationUrl: 'https://example.com/apply'
    },
    {
        id: '4',
        title: 'Backend Engineer',
        company: 'DataFlow Systems',
        location: 'Austin, TX',
        type: 'full-time',
        remote: true,
        salary: { min: 100000, max: 150000, currency: 'USD' },
        description: 'Build scalable backend systems for our data platform...',
        requirements: ['Python', 'Django', 'PostgreSQL', 'Docker'],
        posted: new Date('2024-11-18'),
        applicationUrl: 'https://example.com/apply'
    },
    {
        id: '5',
        title: 'Software Engineering Intern',
        company: 'Innovation Corp',
        location: 'Boston, MA',
        type: 'internship',
        remote: false,
        description: 'Summer internship opportunity for students...',
        requirements: ['Computer Science student', 'JavaScript', 'Git'],
        posted: new Date('2024-11-15'),
        applicationUrl: 'https://example.com/apply'
    }
];

const JobSearch: React.FC = () => {
    const { t } = useLanguage();
    const [searchQuery, setSearchQuery] = useState('');
    const [locationFilter, setLocationFilter] = useState('');
    const [typeFilter, setTypeFilter] = useState<string>('all');
    const [remoteOnly, setRemoteOnly] = useState(false);

    // Filter jobs based on search criteria
    const filteredJobs = useMemo(() => {
        return MOCK_JOBS.filter(job => {
            // Text search (title, company, description)
            const searchLower = searchQuery.toLowerCase();
            const matchesSearch = !searchQuery ||
                job.title.toLowerCase().includes(searchLower) ||
                job.company.toLowerCase().includes(searchLower) ||
                job.description.toLowerCase().includes(searchLower);

            // Location filter
            const matchesLocation = !locationFilter ||
                job.location.toLowerCase().includes(locationFilter.toLowerCase());

            // Job type filter
            const matchesType = typeFilter === 'all' || job.type === typeFilter;

            // Remote filter
            const matchesRemote = !remoteOnly || job.remote;

            return matchesSearch && matchesLocation && matchesType && matchesRemote;
        });
    }, [searchQuery, locationFilter, typeFilter, remoteOnly]);

    const formatSalary = (salary: Job['salary']) => {
        if (!salary) return null;
        const formatter = new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: salary.currency,
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        });
        return `${formatter.format(salary.min)} - ${formatter.format(salary.max)}`;
    };

    const formatDate = (date: Date) => {
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
    };

    const clearFilters = () => {
        setSearchQuery('');
        setLocationFilter('');
        setTypeFilter('all');
        setRemoteOnly(false);
    };

    return (
        <div style={{ width: '100%', margin: 0, padding: 0 }}>
            <Header />
            <div style={{
                display: 'grid',
                gridTemplateColumns: '320px 1fr',
                gap: 0,
                minHeight: 'calc(100vh - 60px)',
                width: '100vw',
                maxWidth: '100%'
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
                                Search
                            </label>
                            <input
                                type="text"
                                className="nb-input"
                                placeholder={t('jobs.search_placeholder')}
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                style={{ width: '100%' }}
                            />
                        </div>

                        {/* Location Filter */}
                        <div>
                            <label style={{
                                display: 'block',
                                marginBottom: '0.5rem',
                                fontSize: '0.875rem',
                                fontWeight: 600,
                                opacity: 0.8
                            }}>
                                {t('jobs.location_filter')}
                            </label>
                            <input
                                type="text"
                                className="nb-input"
                                placeholder={t('jobs.location_filter')}
                                value={locationFilter}
                                onChange={(e) => setLocationFilter(e.target.value)}
                                style={{ width: '100%' }}
                            />
                        </div>

                        {/* Job Type Filter */}
                        <div>
                            <label style={{
                                display: 'block',
                                marginBottom: '0.5rem',
                                fontSize: '0.875rem',
                                fontWeight: 600,
                                opacity: 0.8
                            }}>
                                Job Type
                            </label>
                            <select
                                className="nb-input"
                                value={typeFilter}
                                onChange={(e) => setTypeFilter(e.target.value)}
                                style={{ width: '100%' }}
                            >
                                <option value="all">{t('jobs.type_all')}</option>
                                <option value="full-time">{t('jobs.type_fulltime')}</option>
                                <option value="part-time">{t('jobs.type_parttime')}</option>
                                <option value="contract">{t('jobs.type_contract')}</option>
                                <option value="internship">{t('jobs.type_internship')}</option>
                            </select>
                        </div>

                        {/* Remote Only Checkbox */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.5rem' }}>
                            <input
                                type="checkbox"
                                id="remote-only"
                                checked={remoteOnly}
                                onChange={(e) => setRemoteOnly(e.target.checked)}
                                style={{ cursor: 'pointer' }}
                            />
                            <label htmlFor="remote-only" style={{ cursor: 'pointer', userSelect: 'none', fontSize: '0.875rem' }}>
                                {t('jobs.remote_only')}
                            </label>
                        </div>

                        {/* Clear Filters Button */}
                        {(searchQuery || locationFilter || typeFilter !== 'all' || remoteOnly) && (
                            <div style={{ marginTop: '1rem' }}>
                                <button
                                    onClick={clearFilters}
                                    className="nb-btn-secondary"
                                    style={{ fontSize: '0.875rem', width: '100%' }}
                                >
                                    {t('jobs.clear_filters')}
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
                            {t('jobs.results_count').replace('{count}', filteredJobs.length.toString())}
                        </div>
                    </div>
                </div>

                {/* Right Side - Job Listings */}
                <div style={{
                    padding: '1.5rem',
                    overflowY: 'auto',
                    height: 'calc(100vh - 60px)'
                }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxWidth: '1200px' }}>
                        {filteredJobs.length === 0 ? (
                            <div className="nb-card" style={{ textAlign: 'center', padding: '3rem 1rem' }}>
                                <p style={{ fontSize: '1.125rem', margin: 0, opacity: 0.7 }}>
                                    {t('jobs.no_results')}
                                </p>
                            </div>
                        ) : (
                            filteredJobs.map(job => (
                                <div key={job.id} className="nb-card" style={{ cursor: 'pointer' }}>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                        {/* Job Header */}
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem' }}>
                                            <div style={{ flex: 1 }}>
                                                <h3 style={{ margin: '0 0 0.25rem 0', fontSize: '1.25rem' }}>
                                                    {job.title}
                                                </h3>
                                                <p style={{ margin: 0, fontSize: '1rem', opacity: 0.8 }}>
                                                    {job.company}
                                                </p>
                                            </div>
                                            {job.salary && (
                                                <div style={{
                                                    fontWeight: 600,
                                                    color: 'var(--nb-accent)',
                                                    textAlign: 'right',
                                                    fontSize: '1rem'
                                                }}>
                                                    {formatSalary(job.salary)}
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
                                            <span>📍 {job.location}</span>
                                            <span>•</span>
                                            <span>💼 {t(`jobs.type_${job.type.replace('-', '')}`)}</span>
                                            {job.remote && (
                                                <>
                                                    <span>•</span>
                                                    <span>🏠 {t('jobs.remote')}</span>
                                                </>
                                            )}
                                            <span>•</span>
                                            <span>📅 {formatDate(job.posted)}</span>
                                        </div>

                                        {/* Job Description */}
                                        <p style={{ margin: 0, lineHeight: 1.6 }}>
                                            {job.description}
                                        </p>

                                        {/* Requirements */}
                                        {job.requirements.length > 0 && (
                                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                                                {job.requirements.map((req, index) => (
                                                    <span
                                                        key={index}
                                                        style={{
                                                            padding: '0.25rem 0.75rem',
                                                            backgroundColor: 'var(--nb-accent)',
                                                            border: 'var(--nb-border) solid var(--nb-fg)',
                                                            borderRadius: '4px',
                                                            fontSize: '0.875rem',
                                                            fontWeight: 500
                                                        }}
                                                    >
                                                        {req}
                                                    </span>
                                                ))}
                                            </div>
                                        )}

                                        {/* Apply Button */}
                                        {job.applicationUrl && (
                                            <div style={{ marginTop: '0.5rem' }}>
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        window.open(job.applicationUrl, '_blank');
                                                    }}
                                                    className="nb-btn"
                                                >
                                                    {t('jobs.apply')}
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default JobSearch;
