import React, { useState } from "react";
import "./jobOffersCard.css";

interface JobOffer {
    position: number;
    title: string;
    company: string;
    location: string;
    score: number;
    match_reasons: string[];
    concerns?: string[];
}

const JobOffersCard: React.FC = () => {
    const [offers, setOffers] = useState<JobOffer[]>([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

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
                throw new Error(err.detail || "Failed to generate offers");
            }

            const data = await response.json();
            if (data.offers && Array.isArray(data.offers)) {
                setOffers(data.offers);
                setCurrentIndex(0);
            }
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : "Error generating offers";
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
                <h2 className="home-card-title">Optimal Offers</h2>
                <p className="nb-text-dim">Upload a CV and run profile matching to see offers.</p>
                <button onClick={generateOffers} className="nb-btn nb-btn--accent">
                    Find Offers
                </button>
            </div>
        );
    }

    return (
        <div className="nb-card home-card job-offers-card">
            <h2 className="home-card-title">Optimal Offers</h2>

            {loading && <p className="nb-text-dim">Loading offers...</p>}

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
                            <div className="offer-card">
                                {(() => {
                                    const offer = offers[currentIndex];
                                    return (
                                        <>
                                            <div className="offer-header">
                                                <h3 className="offer-title">{offer.title}</h3>
                                                <div className="offer-score">{offer.score}</div>
                                            </div>
                                            <p className="offer-company">{offer.company}</p>
                                            <p className="offer-location">{offer.location}</p>

                                            <div className="offer-section">
                                                <h4 className="offer-label">Why Match</h4>
                                                <ul className="offer-list">
                                                    {offer.match_reasons.map((reason, i) => (
                                                        <li key={i}>{reason}</li>
                                                    ))}
                                                </ul>
                                            </div>

                                            {offer.concerns && offer.concerns.length > 0 && (
                                                <div className="offer-section">
                                                    <h4 className="offer-label offer-label--concern">Concerns</h4>
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
                    Refresh Offers
                </button>
            )}
        </div>
    );
};

export default JobOffersCard;
