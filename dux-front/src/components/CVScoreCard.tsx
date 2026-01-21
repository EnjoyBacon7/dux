import React, { useState, useEffect, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useLanguage } from "../contexts/useLanguage";

interface EvaluationScores {
    overall_score: number | null;
    completeness_score: number | null;
    experience_quality_score: number | null;
    skills_relevance_score: number | null;
    impact_evidence_score: number | null;
    clarity_score: number | null;
    consistency_score: number | null;
}

interface EvaluationFeedback {
    recommendations: string[];
}

interface Evaluation {
    id: number;
    scores: EvaluationScores;
    feedback: EvaluationFeedback;
    created_at: string | null;
}

interface CVScoreCardProps {
    hasCv: boolean;
    refreshTrigger?: number; // Increment to trigger refresh after upload
}

const POLL_INTERVAL = 5000; // 5 seconds
const MAX_POLL_DURATION = 180000; // 3 minutes

const CVScoreCard: React.FC<CVScoreCardProps> = ({ hasCv, refreshTrigger = 0 }) => {
    const { t } = useLanguage();
    const navigate = useNavigate();
    const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
    // Start with loading=true if user has CV, so we show spinner until fetch completes
    const [isLoading, setIsLoading] = useState(hasCv);
    const [isEvaluating, setIsEvaluating] = useState(false);
    const [isReEvaluating, setIsReEvaluating] = useState(false);
    const [isHovered, setIsHovered] = useState(false);
    // Track if we've checked for evaluation (to show "no evaluation" state vs loading)
    const [hasChecked, setHasChecked] = useState(false);
    const pollStartTime = useRef<number | null>(null);
    const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

    const handleViewProfileHub = () => {
        navigate("/profile-hub");
    };

    const fetchEvaluation = useCallback(async (): Promise<Evaluation | null> => {
        try {
            const response = await fetch("/api/cv/evaluation");
            if (response.ok) {
                const data = await response.json();
                return data;
            }
            return null;
        } catch {
            return null;
        }
    }, []);

    const stopPolling = useCallback(() => {
        if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
        }
        pollStartTime.current = null;
    }, []);

    const startPolling = useCallback(() => {
        stopPolling();
        pollStartTime.current = Date.now();
        setIsEvaluating(true);

        pollIntervalRef.current = setInterval(async () => {
            // Check if we've exceeded max poll duration
            if (pollStartTime.current && Date.now() - pollStartTime.current > MAX_POLL_DURATION) {
                stopPolling();
                setIsEvaluating(false);
                return;
            }

            const result = await fetchEvaluation();
            if (result) {
                setEvaluation(result);
                stopPolling();
                setIsEvaluating(false);
            }
        }, POLL_INTERVAL);
    }, [fetchEvaluation, stopPolling]);

    // Initial fetch and refresh when CV is uploaded
    useEffect(() => {
        if (!hasCv) {
            setEvaluation(null);
            setHasChecked(false);
            setIsLoading(false);
            stopPolling();
            return;
        }

        const loadEvaluation = async () => {
            setIsLoading(true);
            setHasChecked(false);
            const result = await fetchEvaluation();
            setIsLoading(false);
            setHasChecked(true);

            if (result) {
                setEvaluation(result);
            } else {
                // No evaluation found - don't auto-poll, show "no evaluation" state
                setEvaluation(null);
            }
        };

        loadEvaluation();

        return () => stopPolling();
    }, [hasCv, refreshTrigger, fetchEvaluation, stopPolling]);

    const handleReEvaluate = async () => {
        if (isReEvaluating || !hasCv) return;

        setIsReEvaluating(true);
        try {
            const response = await fetch("/api/cv/evaluate", {
                method: "POST",
            });

            if (response.ok) {
                // Start polling for the new evaluation
                setEvaluation(null);
                setIsReEvaluating(false);
                startPolling();
            } else {
                setIsReEvaluating(false);
            }
        } catch {
            setIsReEvaluating(false);
        }
    };

    // Get score color based on value
    const getScoreColor = (score: number): string => {
        if (score < 50) return "var(--nb-danger)";
        if (score < 70) return "var(--nb-warning)";
        return "var(--nb-success)";
    };

    // Calculate SVG circle parameters
    const circleRadius = 45;
    const circumference = 2 * Math.PI * circleRadius;
    const scorePercent = evaluation?.scores.overall_score ?? 0;
    const strokeDashoffset = circumference - (scorePercent / 100) * circumference;

    // Dimension scores for mini bars
    const dimensionScores = evaluation ? [
        { key: "completeness", label: t("cv_score.completeness"), score: evaluation.scores.completeness_score },
        { key: "experience", label: t("cv_score.experience"), score: evaluation.scores.experience_quality_score },
        { key: "skills", label: t("cv_score.skills"), score: evaluation.scores.skills_relevance_score },
        { key: "impact", label: t("cv_score.impact"), score: evaluation.scores.impact_evidence_score },
        { key: "clarity", label: t("cv_score.clarity"), score: evaluation.scores.clarity_score },
        { key: "consistency", label: t("cv_score.consistency"), score: evaluation.scores.consistency_score },
    ] : [];

    // Render no CV state
    if (!hasCv) {
        return (
            <div className="nb-card home-card cv-score-card">
                <div className="cv-score-header">
                    <h2 className="home-card-title">{t("cv_score.title")}</h2>
                </div>
                <div 
                    className="cv-score-body"
                    onMouseEnter={() => setIsHovered(true)}
                    onMouseLeave={() => setIsHovered(false)}
                >
                    <div className={`cv-score-body-content ${isHovered ? "blurred" : ""}`}>
                        <p className="cv-score-empty">{t("cv_score.no_cv")}</p>
                    </div>
                    <div className={`cv-score-hover-overlay ${isHovered ? "visible" : ""}`}>
                        <button className="nb-btn nb-btn--accent cv-score-hub-btn" onClick={handleViewProfileHub}>
                            {t("cv_score.view_profile_hub")}
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    // Render loading/evaluating state
    if (isLoading || isEvaluating) {
        return (
            <div className="nb-card home-card cv-score-card">
                <div className="cv-score-header">
                    <h2 className="home-card-title">{t("cv_score.title")}</h2>
                    <button
                        className="cv-score-refresh-btn"
                        onClick={handleReEvaluate}
                        disabled={isReEvaluating || isEvaluating}
                        title={t("cv_score.re_evaluate")}
                    >
                        <svg
                            className={`cv-score-refresh-icon ${isEvaluating ? "spinning" : ""}`}
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                        >
                            <path d="M23 4v6h-6M1 20v-6h6" />
                            <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" />
                        </svg>
                    </button>
                </div>
                <div 
                    className="cv-score-body"
                    onMouseEnter={() => setIsHovered(true)}
                    onMouseLeave={() => setIsHovered(false)}
                >
                    <div className={`cv-score-body-content ${isHovered ? "blurred" : ""}`}>
                        <div className="cv-score-evaluating">
                            <div className="cv-score-spinner"></div>
                            <p>{t("cv_score.evaluating")}</p>
                        </div>
                    </div>
                    <div className={`cv-score-hover-overlay ${isHovered ? "visible" : ""}`}>
                        <button className="nb-btn nb-btn--accent cv-score-hub-btn" onClick={handleViewProfileHub}>
                            {t("cv_score.view_profile_hub")}
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    // Render "no evaluation yet" state - CV exists but no evaluation has been run
    // No hover overlay here - the primary action is to evaluate
    if (hasChecked && !evaluation) {
        return (
            <div className="nb-card home-card cv-score-card">
                <div className="cv-score-header">
                    <h2 className="home-card-title">{t("cv_score.title")}</h2>
                </div>
                <div className="cv-score-body">
                    <div className="cv-score-body-content">
                        <div className="cv-score-no-evaluation">
                            <p>{t("cv_score.no_evaluation")}</p>
                            <button 
                                className="nb-btn nb-btn--accent"
                                onClick={handleReEvaluate}
                                disabled={isReEvaluating}
                            >
                                {isReEvaluating ? t("cv_score.evaluating") : t("cv_score.evaluate_now")}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    // Render complete state with scores
    return (
        <div className="nb-card home-card cv-score-card">
            <div className="cv-score-header">
                <h2 className="home-card-title">{t("cv_score.title")}</h2>
                <button
                    className="cv-score-refresh-btn"
                    onClick={handleReEvaluate}
                    disabled={isReEvaluating}
                    title={t("cv_score.re_evaluate")}
                >
                    <svg
                        className={`cv-score-refresh-icon ${isReEvaluating ? "spinning" : ""}`}
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                    >
                        <path d="M23 4v6h-6M1 20v-6h6" />
                        <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" />
                    </svg>
                </button>
            </div>

            <div 
                className="cv-score-body"
                onMouseEnter={() => setIsHovered(true)}
                onMouseLeave={() => setIsHovered(false)}
            >
                <div className={`cv-score-body-content ${isHovered ? "blurred" : ""}`}>
                    <div className="cv-score-content">
                        {/* Score Circle */}
                        <div className="cv-score-circle-container">
                            <svg className="cv-score-circle" viewBox="0 0 100 100">
                                {/* Background circle */}
                                <circle
                                    cx="50"
                                    cy="50"
                                    r={circleRadius}
                                    fill="none"
                                    stroke="var(--nb-bg-muted)"
                                    strokeWidth="8"
                                />
                                {/* Score circle */}
                                <circle
                                    cx="50"
                                    cy="50"
                                    r={circleRadius}
                                    fill="none"
                                    stroke={getScoreColor(scorePercent)}
                                    strokeWidth="8"
                                    strokeLinecap="round"
                                    strokeDasharray={circumference}
                                    strokeDashoffset={strokeDashoffset}
                                    transform="rotate(-90 50 50)"
                                    className="cv-score-circle-progress"
                                />
                                {/* Score text */}
                                <text
                                    x="50"
                                    y="50"
                                    textAnchor="middle"
                                    dy="0.35em"
                                    className="cv-score-text"
                                >
                                    {scorePercent}
                                </text>
                            </svg>
                        </div>

                        {/* Dimension Scores */}
                        <div className="cv-score-dimensions">
                            {dimensionScores.map(({ key, label, score }) => (
                                <div key={key} className="cv-score-dimension">
                                    <div className="cv-score-dimension-header">
                                        <span className="cv-score-dimension-label">{label}</span>
                                        <span className="cv-score-dimension-value">{score ?? "-"}</span>
                                    </div>
                                    <div className="cv-score-bar-bg">
                                        <div
                                            className="cv-score-bar-fill"
                                            style={{
                                                width: `${score ?? 0}%`,
                                                backgroundColor: getScoreColor(score ?? 0),
                                            }}
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Recommendations */}
                    {evaluation?.feedback.recommendations && evaluation.feedback.recommendations.length > 0 && (
                        <div className="cv-score-recommendations">
                            <h3 className="cv-score-recommendations-title">{t("cv_score.recommendations")}</h3>
                            <ul className="cv-score-recommendations-list">
                                {evaluation.feedback.recommendations.slice(0, 3).map((rec, idx) => (
                                    <li key={idx}>{rec}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>

                <div className={`cv-score-hover-overlay ${isHovered ? "visible" : ""}`}>
                    <button className="nb-btn nb-btn--accent cv-score-hub-btn" onClick={handleViewProfileHub}>
                        {t("cv_score.view_profile_hub")}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default CVScoreCard;
