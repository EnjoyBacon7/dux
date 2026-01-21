import React, { useState } from "react";
import { useLanguage } from "../contexts/useLanguage";
import "./jobOffersCard.css";
import OfferBox from "./OfferBox";
import JobDetail from "./JobDetail";
import type { JobOffer as FullJobOffer } from "./JobDetail";

interface OptimalOffer {
    position: number;
    job_id?: string;
    title: string;
    company: string;
    location: string;
    score: number;
    match_reasons: string[];
    concerns?: string[];
    job_data?: FullJobOffer;
}

const JobOffersCard: React.FC = () => {
    const { t } = useLanguage();
    const [offers, setOffers] = useState<OptimalOffer[]>([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [selectedOffer, setSelectedOffer] = useState<OptimalOffer | null>(null);

    const generateOffers = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch("/api/chat/match_profile", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify({}),
            });

            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                throw new Error(err.detail || t('errors.failed_generate_offers'));
            }

            const data = await response.json();
            if (data.offers && Array.isArray(data.offers)) {
                setOffers(data.offers);
                setCurrentIndex(0);
            }
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : t('errors.error_generating_offers');
            setError(message);
        } finally {
            setLoading(false);
        }
    };

    const handlePrev = () => {
        setCurrentIndex((prev) => (prev === 0 ? offers.length - 1 : prev - 1));
    };

    const handleNext = () => {
        setCurrentIndex((prev) => (prev === offers.length - 1 ? 0 : prev + 1));
    };

    // Helper to get job data for display
    const getJobDisplayData = (offer: OptimalOffer) => {
        const jobData = offer.job_data;
        return {
            title: jobData?.intitule || offer.title,
            company: jobData?.entreprise_nom || offer.company,
            location: jobData?.lieuTravail_libelle || offer.location,
            contractType: jobData?.typeContratLibelle || undefined,
            date: jobData?.dateActualisation || jobData?.dateCreation || undefined,
            description: jobData?.description || undefined,
            salary: jobData?.salaire_libelle || undefined,
        };
    };

    if (offers.length === 0 && !loading && !error) {
        return (
            <div className="nb-card home-card job-offers-card">
                <h2 className="home-card-title">{t('jobs.optimal_offers')}</h2>
                <p className="nb-text-dim">{t('jobs.upload_cv_to_match')}</p>
                <button onClick={generateOffers} className="nb-btn nb-btn--accent">
                    {t('jobs.find_offers')}
                </button>
            </div>
        );
    }

    return (
        <div className="nb-card home-card job-offers-card">
            <h2 className="home-card-title">{t('jobs.optimal_offers')}</h2>

            {loading && <p className="nb-text-dim">{t('jobs.loading_offers')}</p>}

            {error && (
                <div className="nb-alert nb-alert--danger">
                    {error}
                </div>
            )}

            {offers.length > 0 && (
                <div className="job-offers-carousel">
                    <div className="carousel-container">
                        <button
                            onClick={handlePrev}
                            className="carousel-btn carousel-btn--prev"
                            disabled={offers.length === 1}
                        >
                            ◀
                        </button>

                        <div className="carousel-content">
                            <div className="nb-card" style={{ width: '100%' }}>
                                {(() => {
                                    const offer = offers[currentIndex];
                                    const displayData = getJobDisplayData(offer);
                                    return (
                                        <>
                                            {/* Use standard offer box layout with full job data */}
                                            <OfferBox
                                                title={displayData.title}
                                                company={displayData.company}
                                                location={displayData.location}
                                                contractType={displayData.contractType}
                                                date={displayData.date}
                                                salary={displayData.salary}
                                                showViewButton={false}
                                                onClick={() => setSelectedOffer(offer)}
                                            />

                                            {/* Match score badge */}
                                            <div className="offer-score-badge" style={{
                                                marginTop: '0.75rem',
                                                padding: '0.5rem',
                                                backgroundColor: 'var(--nb-accent)',
                                                borderRadius: '4px',
                                                textAlign: 'center',
                                                fontWeight: 600
                                            }}>
                                                {t('jobs.match_score')}: {offer.score}/100
                                            </div>

                                            {/* Why match / concerns sections below the standard box */}
                                            <div className="offer-section">
                                                <h4 className="offer-label">{t('jobs.why_match')}</h4>
                                                <ul className="offer-list">
                                                    {offer.match_reasons.map((reason, i) => (
                                                        <li key={i}>{reason}</li>
                                                    ))}
                                                </ul>
                                            </div>

                                            {offer.concerns && offer.concerns.length > 0 && (
                                                <div className="offer-section">
                                                    <h4 className="offer-label offer-label--concern">{t('jobs.concerns')}</h4>
                                                    <ul className="offer-list">
                                                        {offer.concerns.map((concern, i) => (
                                                            <li key={i}>{concern}</li>
                                                        ))}
                                                    </ul>
                                                </div>
                                            )}
                                        </>
                                    );
                                })()}
                            </div>
                        </div>

                        <button
                            onClick={handleNext}
                            className="carousel-btn carousel-btn--next"
                            disabled={offers.length === 1}
                        >
                            ▶
                        </button>
                    </div>

                    <div className="carousel-indicators">
                        {offers.map((_, index) => (
                            <button
                                key={index}
                                className={`indicator ${index === currentIndex ? "active" : ""}`}
                                onClick={() => setCurrentIndex(index)}
                            />
                        ))}
                    </div>
                </div>
            )}

            {offers.length > 0 && !loading && (
                <button onClick={generateOffers} className="nb-btn nb-btn--ghost nb-mt">
                    {t('jobs.refresh_offers')}
                </button>
            )}

            {/* Use JobDetail when job_data is available, fallback to simple modal otherwise */}
            {selectedOffer && selectedOffer.job_data && (
                <JobDetail
                    job={selectedOffer.job_data}
                    onClose={() => setSelectedOffer(null)}
                />
            )}

            {/* Fallback modal for offers without full job_data */}
            {selectedOffer && !selectedOffer.job_data && (
                <div className="nb-modal-backdrop" onClick={() => setSelectedOffer(null)}>
                    <div
                        className="nb-card"
                        style={{ maxWidth: '520px', width: '90%', margin: '5vh auto', position: 'relative' }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <button
                            aria-label="Close"
                            className="nb-btn nb-btn--ghost"
                            style={{ position: 'absolute', top: '0.75rem', right: '0.75rem' }}
                            onClick={() => setSelectedOffer(null)}
                        >
                            ✕
                        </button>

                        <OfferBox
                            title={selectedOffer.title}
                            company={selectedOffer.company}
                            location={selectedOffer.location}
                            showViewButton={false}
                        />

                        <div className="offer-score-badge" style={{
                            marginTop: '0.75rem',
                            padding: '0.5rem',
                            backgroundColor: 'var(--nb-accent)',
                            borderRadius: '4px',
                            textAlign: 'center',
                            fontWeight: 600
                        }}>
                            {t('jobs.match_score')}: {selectedOffer.score}/100
                        </div>

                        <div className="offer-section" style={{ marginTop: '1rem' }}>
                            <h4 className="offer-label">{t('jobs.why_match')}</h4>
                            <ul className="offer-list">
                                {selectedOffer.match_reasons.map((reason, i) => (
                                    <li key={i}>{reason}</li>
                                ))}
                            </ul>
                        </div>

                        {selectedOffer.concerns && selectedOffer.concerns.length > 0 && (
                            <div className="offer-section">
                                <h4 className="offer-label offer-label--concern">{t('jobs.concerns')}</h4>
                                <ul className="offer-list">
                                    {selectedOffer.concerns.map((concern, i) => (
                                        <li key={i}>{concern}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default JobOffersCard;
