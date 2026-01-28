import React, { useState } from "react";
import { useLanguage } from "../contexts/useLanguage";
import OfferBox from "./OfferBox";
import JobDetail from "./JobDetail";
import type { JobOffer, JobMatchMetadata } from "../types/job";
import styles from "../styles/JobOffersCard.module.css";

// Merged type with both job data and match metadata
type DisplayOffer = JobOffer & JobMatchMetadata;

const JobOffersCard: React.FC = () => {
    const { t } = useLanguage();
    const [offers, setOffers] = useState<DisplayOffer[]>([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [selectedOffer, setSelectedOffer] = useState<DisplayOffer | null>(null);

    // Fetch full job data by job_id
    const fetchJobData = async (job_id: string): Promise<JobOffer | null> => {
        try {
            const response = await fetch(`/api/jobs/offer/${job_id}`, {
                credentials: "include",
            });
            if (!response.ok) {
                console.error(`Failed to fetch job data for ${job_id}`);
                return null;
            }
            const data = await response.json();
            return data.offer;
        } catch (err) {
            console.error(`Error fetching job data for ${job_id}:`, err);
            return null;
        }
    };

    // Merge optimal offer metadata with full job data
    const mergeOfferData = async (optimalOffer: any): Promise<DisplayOffer> => {
        if (!optimalOffer.job_id) {
            return optimalOffer as DisplayOffer;
        }

        const jobData = await fetchJobData(optimalOffer.job_id);
        if (jobData) {
            return {
                ...jobData,
                ...optimalOffer, // Preserve optimal offer metadata
            } as DisplayOffer;
        }
        return optimalOffer as DisplayOffer;
    };

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
                // Fetch full job data for each offer
                const mergedOffers = await Promise.all(
                    data.offers.map((offer: any) => mergeOfferData(offer))
                );
                setOffers(mergedOffers);
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

    if (offers.length === 0 && !loading && !error) {
        return (
            <div className="nb-card home-card job-offers-card">
                <h2 className="home__card-title">{t('jobs.optimal_offers')}</h2>
                <p className="nb-text-dim">{t('jobs.upload_cv_to_match')}</p>
                <button onClick={generateOffers} className="nb-btn nb-btn--accent">
                    {t('jobs.find_offers')}
                </button>
            </div>
        );
    }

    return (
        <div className="nb-card home-card job-offers-card">
            <h2 className="home__card-title">{t('jobs.optimal_offers')}</h2>

            {loading && <p className="nb-text-dim">{t('jobs.loading_offers')}</p>}

            {error && (
                <div className="nb-alert nb-alert--danger">
                    {error}
                </div>
            )}

            {offers.length > 0 && (
                <div className={styles["job-offers__carousel"]}>
                    <div className={styles["job-offers__carousel-container"]}>
                        <button
                            onClick={handlePrev}
                            className={styles["job-offers__carousel-btn"]}
                            disabled={offers.length === 1}
                        >
                            ◀
                        </button>

                        <div className={styles["job-offers__carousel-content"]}>
                            <div className="nb-card">
                                {(() => {
                                    const offer = offers[currentIndex];
                                    return (
                                        <>
                                            {/* Use standard offer box layout - same as JobSearch */}
                                            <OfferBox
                                                title={offer.intitule || t('jobs.untitled')}
                                                company={offer.entreprise_nom ?? undefined}
                                                location={offer.lieuTravail_libelle ?? undefined}
                                                contractType={offer.typeContratLibelle ?? undefined}
                                                date={offer.dateActualisation || offer.dateCreation || undefined}
                                                salary={offer.salaire_libelle ?? undefined}
                                                showViewButton={false}
                                                onClick={() => setSelectedOffer(offer)}
                                            />

                                            {/* Match score badge */}
                                            <div className={styles["job-offers__score-badge"]}>
                                                {t('jobs.match_score')}: {offer.score}/100
                                            </div>

                                            {/* Why match / concerns sections below the standard box */}
                                            <div className={styles["job-offers__section"]}>
                                                <h4 className={styles["job-offers__label"]}>{t('jobs.why_match')}</h4>
                                                <ul className={styles["job-offers__list"]}>
                                                    {offer.match_reasons.map((reason: string, i: number) => (
                                                        <li key={i}>{reason}</li>
                                                    ))}
                                                </ul>
                                            </div>

                                            {offer.concerns && offer.concerns.length > 0 && (
                                                <div className={styles["job-offers__section"]}>
                                                    <h4 className={`${styles["job-offers__label"]} ${styles["job-offers__label--concern"]}`}>{t('jobs.concerns')}</h4>
                                                    <ul className={styles["job-offers__list"]}>
                                                        {offer.concerns.map((concern: string, i: number) => (
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
                            className={styles["job-offers__carousel-btn"]}
                            disabled={offers.length === 1}
                        >
                            ▶
                        </button>
                    </div>

                    <div className={styles["job-offers__carousel-indicators"]}>
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

            {/* Use JobDetail for the selected offer - same component as JobSearch */}
            {selectedOffer && (
                <JobDetail
                    job={selectedOffer}
                    onClose={() => setSelectedOffer(null)}
                />
            )}
        </div>
    );
};

export default JobOffersCard;
