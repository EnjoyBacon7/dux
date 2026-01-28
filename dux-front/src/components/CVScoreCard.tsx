import React, { useState, useEffect, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useLanguage } from "../contexts/useLanguage";
import styles from "../styles/CVScoreCard.module.css";

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

interface VisualAnalysis {
    visual_strengths: string[];
    visual_weaknesses: string[];
    visual_recommendations: string[];
    layout_assessment?: string;
    typography_assessment?: string;
    readability_assessment?: string;
    image_quality_notes?: string[];
}

interface Evaluation {
    id: number;
    scores: EvaluationScores;
    feedback: EvaluationFeedback;
    visual_analysis?: VisualAnalysis | null;
    merged_recommendations?: string[]; // Top prioritized recommendations from both LLM and VLM
    created_at: string | null;
    evaluation_status: string | null; // "pending", "completed", "failed"
    error_message: string | null;
}

interface CVScoreCardProps {
    hasCv: boolean;
    refreshTrigger?: number; // Increment to trigger refresh after upload
}

const POLL_INTERVAL = 3000; // 3 seconds - faster polling for better UX
const MAX_POLL_DURATION = 180000; // 3 minutes

const CVScoreCard: React.FC<CVScoreCardProps> = ({ hasCv, refreshTrigger = 0 }) => {
    const { t } = useLanguage();
    const navigate = useNavigate();
    const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
    // Start with loading=true if user has CV, so we show spinner until fetch completes
    const [isLoading, setIsLoading] = useState(hasCv);
    const [isEvaluating, setIsEvaluating] = useState(false);
    const [isReEvaluating, setIsReEvaluating] = useState(false);
    // Track if we've checked for evaluation (to show "no evaluation" state vs loading)
    const [hasChecked, setHasChecked] = useState(false);
    // Track the previous refresh trigger to detect new uploads
    const prevRefreshTrigger = useRef(refreshTrigger);
    const pollStartTime = useRef<number | null>(null);
    const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

    const handleViewProfileHub = () => {
        navigate("/profile-hub");
    };

    const fetchEvaluation = useCallback(async (): Promise<Evaluation | null> => {
        try {
            const response = await fetch("/api/cv/evaluation", {
                credentials: "include",
            });
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
        setHasChecked(false); // Reset so we show evaluating state

        // Do an immediate first check
        const checkAndPoll = async () => {
            const result = await fetchEvaluation();
            if (result) {
                setEvaluation(result);
                setHasChecked(true);
                // Stop polling only if evaluation is completed or failed
                if (result.evaluation_status === "completed" || result.evaluation_status === "failed") {
                    stopPolling();
                    setIsEvaluating(false);
                    return true; // Done
                }
            }
            return false; // Continue polling
        };

        // Check immediately first
        checkAndPoll();

        // Then set up interval for subsequent checks
        pollIntervalRef.current = setInterval(async () => {
            // Check if we've exceeded max poll duration
            if (pollStartTime.current && Date.now() - pollStartTime.current > MAX_POLL_DURATION) {
                stopPolling();
                setIsEvaluating(false);
                setHasChecked(true);
                return;
            }

            await checkAndPoll();
        }, POLL_INTERVAL);
    }, [fetchEvaluation, stopPolling]);

    // Initial fetch and refresh when CV is uploaded
    useEffect(() => {
        if (!hasCv) {
            setEvaluation(null);
            setHasChecked(false);
            setIsLoading(false);
            setIsEvaluating(false);
            stopPolling();
            prevRefreshTrigger.current = refreshTrigger;
            return;
        }

        // Detect if this is a new CV upload (refreshTrigger changed)
        const isNewUpload = refreshTrigger > prevRefreshTrigger.current;
        prevRefreshTrigger.current = refreshTrigger;

        if (isNewUpload) {
            // New CV upload - clear old evaluation and start polling immediately
            // The backend will create a pending evaluation record
            setEvaluation(null);
            setHasChecked(false);
            setIsLoading(false);
            startPolling(); // Start polling immediately, don't wait for initial fetch
            return;
        }

        // Initial load (not a new upload) - fetch current evaluation status
        const loadEvaluation = async () => {
            setIsLoading(true);
            setHasChecked(false);
            const result = await fetchEvaluation();
            setIsLoading(false);
            setHasChecked(true);

            if (result) {
                setEvaluation(result);
                // If evaluation is pending, start polling for updates
                if (result.evaluation_status === "pending") {
                    startPolling();
                } else {
                    setIsEvaluating(false);
                }
            } else {
                // No evaluation found - show "no evaluation" state
                setEvaluation(null);
                setIsEvaluating(false);
            }
        };

        loadEvaluation();

        return () => stopPolling();
    }, [hasCv, refreshTrigger, fetchEvaluation, stopPolling, startPolling]);

    const handleReEvaluate = async () => {
        if (isReEvaluating || isEvaluating || !hasCv) return;

        setIsReEvaluating(true);
        // Clear evaluation immediately so we show evaluating state
        setEvaluation(null);
        
        try {
            const response = await fetch("/api/cv/evaluate", {
                method: "POST",
                credentials: "include",
            });

            if (response.ok) {
                // Start polling for the new evaluation
                setIsReEvaluating(false);
                startPolling();
            } else {
                setIsReEvaluating(false);
                // Re-fetch the current evaluation since we cleared it
                const current = await fetchEvaluation();
                if (current) {
                    setEvaluation(current);
                }
            }
        } catch {
            setIsReEvaluating(false);
            // Re-fetch the current evaluation since we cleared it
            const current = await fetchEvaluation();
            if (current) {
                setEvaluation(current);
            }
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
                <div className={styles["cv-score__header"]}>
                    <h2 className="home__card-title">{t("cv_score.title")}</h2>
                </div>
                <div className={styles["cv-score__body"]}>
                    <div className={styles["cv-score__body-content"]}>
                        <p className={styles["cv-score__empty"]}>{t("cv_score.no_cv")}</p>
                    </div>
                </div>
            </div>
        );
    }

    // Determine the current state
    const isPending = evaluation?.evaluation_status === "pending";
    const isCompleted = evaluation?.evaluation_status === "completed";
    const isFailed = evaluation?.evaluation_status === "failed";
    
    // Show evaluating state when: loading, polling/evaluating, or status is pending
    // Priority: isEvaluating takes precedence (we know we're actively polling)
    const showEvaluating = isLoading || isEvaluating || isPending;
    
    // Render loading/evaluating state
    if (showEvaluating) {
        return (
            <div className="nb-card home-card cv-score-card">
                <div className={styles["cv-score__header"]}>
                    <h2 className="home__card-title">{t("cv_score.title")}</h2>
                    <button
                        className={styles["cv-score__refresh-btn"]}
                        onClick={handleReEvaluate}
                        disabled={true}
                        title={t("cv_score.re_evaluate")}
                    >
                        <svg
                            className={`${styles["cv-score__refresh-icon"]} ${styles["cv-score__refresh-icon--spinning"]}`}
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
                <div className={styles["cv-score__body"]}>
                    <div className={styles["cv-score__body-content"]}>
                        <div className={styles["cv-score__evaluating"]}>
                            <div className={styles["cv-score__spinner"]}></div>
                            <p>{t("cv_score.evaluating")}</p>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    // Safety check: if we haven't checked yet and not evaluating, show loading
    // This handles edge cases during state transitions
    if (!hasChecked) {
        return (
            <div className="nb-card home-card cv-score-card">
                <div className={styles["cv-score__header"]}>
                    <h2 className="home__card-title">{t("cv_score.title")}</h2>
                </div>
                <div className={styles["cv-score__body"]}>
                    <div className={styles["cv-score__body-content"]}>
                        <div className={styles["cv-score__evaluating"]}>
                            <div className={styles["cv-score__spinner"]}></div>
                            <p>{t("cv_score.evaluating")}</p>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    // Render "no evaluation yet" or "failed" state
    // Show this when: we've checked and either no evaluation exists, or it failed, or not completed
    if (!evaluation || isFailed || !isCompleted) {
        return (
            <div className="nb-card home-card cv-score-card">
                <div className={styles["cv-score__header"]}>
                    <h2 className="home__card-title">{t("cv_score.title")}</h2>
                </div>
                <div className={styles["cv-score__body"]}>
                    <div className={styles["cv-score__body-content"]}>
                        <div className={styles["cv-score__no-evaluation"]}>
                            <p>{isFailed ? t("cv_score.evaluation_failed") : t("cv_score.no_evaluation")}</p>
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

    // Render complete state with scores (only when evaluation_status === "completed")
    return (
        <div className="nb-card home-card cv-score-card">
            <div className={styles["cv-score__header"]}>
                <h2 className="home__card-title">{t("cv_score.title")}</h2>
                <button
                    className={styles["cv-score__refresh-btn"]}
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

            <div className={styles["cv-score__body"]}>
                <div className={styles["cv-score__body-content"]}>
                    <div className={styles["cv-score__content"]}>
                        {/* Score Circle */}
                        <div className={styles["cv-score__circle-container"]}>
                            <svg className={styles["cv-score__circle"]} viewBox="0 0 100 100">
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
                                    className={styles["cv-score__circle-progress"]}
                                />
                                {/* Score text */}
                                <text
                                    x="50"
                                    y="50"
                                    textAnchor="middle"
                                    dy="0.35em"
                                    className={styles["cv-score__text"]}
                                >
                                    {scorePercent}
                                </text>
                            </svg>
                        </div>

                        {/* Dimension Scores */}
                        <div className={styles["cv-score__dimensions"]}>
                            {dimensionScores.map(({ key, label, score }) => (
                                <div key={key} className={styles["cv-score__dimension"]}>
                                    <div className={styles["cv-score__dimension-header"]}>
                                        <span className={styles["cv-score__dimension-label"]}>{label}</span>
                                        <span className={styles["cv-score__dimension-value"]}>{score ?? "-"}</span>
                                    </div>
                                    <div className={styles["cv-score__bar-bg"]}>
                                        <div
                                            className={styles["cv-score__bar-fill"]}
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

                    {/* Recommendations - Use merged recommendations if available, otherwise fallback to LLM recommendations */}
                    {(() => {
                        const recommendations = evaluation?.merged_recommendations && evaluation.merged_recommendations.length > 0
                            ? evaluation.merged_recommendations
                            : (evaluation?.feedback.recommendations || []);
                        
                        return recommendations.length > 0 ? (
                            <div className={styles["cv-score__recommendations"]}>
                                <h3 className={styles["cv-score__recommendations-title"]}>{t("cv_score.recommendations")}</h3>
                                <ul className={styles["cv-score__recommendations-list"]}>
                                    {recommendations.slice(0, 5).map((rec, idx) => (
                                        <li key={idx}>{rec}</li>
                                    ))}
                                </ul>
                            </div>
                        ) : null;
                    })()}

                    {/* Profile Hub Button - shown below score */}
                    <div className={styles["cv-score__actions"]}>
                        <button className="nb-btn nb-btn--accent" onClick={handleViewProfileHub}>
                            {t("cv_score.view_profile_hub")}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default CVScoreCard;
