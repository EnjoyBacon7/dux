import React, { useEffect, useState } from 'react';
import { useLanguage } from '../contexts/useLanguage'; // Import du hook
import type { JobOffer } from './JobDetail';
import styles from '../styles/JobMatchAnalysis.module.css';

interface AnalysisResult {
    score_technique: number;
    score_culturel: number;
    match_reasons: string[];
    missing_skills: string[];
    verdict: string;
}

interface JobMatchAnalysisProps {
    job: JobOffer;
    onClose: () => void;
}

const JobMatchAnalysis: React.FC<JobMatchAnalysisProps> = ({ job, onClose }) => {
    const { t, language } = useLanguage();

    const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchAnalysis = async () => {
            try {
                const payload = {
                    id: job.id,
                    intitule: job.intitule,
                    description: job.description,
                    entreprise_nom: job["entreprise_nom"],
                    competences: job.competences,
                    lang: language // Envoi de la langue au backend
                };

                const response = await fetch(`/api/jobs/analyze`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (!response.ok) throw new Error("Analysis failed");

                const data = await response.json();
                setAnalysis(data.analysis);
            } catch (err) {
                // Utilisation de la nouvelle clé d'erreur
                setError(t('analysis.error'));
            } finally {
                setLoading(false);
            }
        };

        fetchAnalysis();
    }, [job, language]);

    const getScoreColor = (score: number) => {
        if (score >= 75) return '#10B981';
        if (score >= 50) return '#F59E0B';
        return '#EF4444';
    };

    return (
        <div className={styles['jma__overlay']} onClick={onClose}>

            <div className={styles['jma__panel']} onClick={e => e.stopPropagation()}>

                {/* Header */}
                <div className={styles['jma__header']}>
                    <h2 className={styles['jma__title']}>
                        <span>⚡</span> {t('analysis.title')}
                    </h2>
                    <button onClick={onClose} className={`nb-btn-secondary ${styles['jma__close-btn']}`}>✕</button>
                </div>

                <div className={styles['jma__job-ref']}>
                    Ref: {job.intitule}
                </div>

                {loading ? (
                    <div className={styles['jma__loading']}>
                        <div className={styles['jma__spinner']}></div>
                        <p>{t('analysis.loading')}</p>
                    </div>
                ) : error ? (
                    <div className={styles['jma__error']}>
                        <p>{error}</p>
                    </div>
                ) : analysis ? (
                    <div className={styles['jma__content']}>

                        {/* Scores : Utilisation des clés analysis.technical et analysis.culture */}
                        <div className={styles['jma__scores']}>
                            <ScoreCircle label={t('analysis.technical')} score={analysis.score_technique} color={getScoreColor(analysis.score_technique)} />
                            <ScoreCircle label={t('analysis.culture')} score={analysis.score_culturel} color={getScoreColor(analysis.score_culturel)} />
                        </div>

                        {/* Verdict */}
                        <div className={styles['jma__verdict']}>
                            "{analysis.verdict}"
                        </div>

                        <div className={styles['jma__lists']}>
                            {/* Points Forts */}
                            <div>
                                <h3 className={styles['jma__strengths-title']}>
                                    {t('analysis.strengths')}
                                </h3>
                                <ul className={styles['jma__strengths-list']}>
                                    {analysis.match_reasons.map((reason, idx) => (
                                        <li key={idx}>
                                            <span className={styles['jma__strengths-icon']}>✓</span> <span>{reason}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>

                            {/* Points à améliorer */}
                            <div>
                                <h3 className={styles['jma__weaknesses-title']}>
                                    {t('analysis.weaknesses')}
                                </h3>
                                <ul className={styles['jma__weaknesses-list']}>
                                    {analysis.missing_skills.map((skill, idx) => (
                                        <li key={idx}>
                                            <span className={styles['jma__weaknesses-icon']}>•</span> <span>{skill}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    </div>
                ) : null}
            </div>
        </div>
    );
};

// Helper
const ScoreCircle = ({ label, score, color }: { label: string, score: number, color: string }) => (
    <div className={styles['jma__score-circle']}>
        <div 
            className={styles['jma__score-circle-outer']}
            style={{
                background: `conic-gradient(${color} ${score * 3.6}deg, #e5e7eb 0deg)`
            }}
        >
            <div className={styles['jma__score-circle-inner']}>
                <span className={styles['jma__score-value']} style={{ color: color }}>{score}%</span>
            </div>
        </div>
        <span className={styles['jma__score-label']}>{label}</span>
    </div>
);

export default JobMatchAnalysis;