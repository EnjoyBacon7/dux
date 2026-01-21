import React, { useEffect, useState } from 'react';
import { useLanguage } from '../contexts/useLanguage'; // Import du hook
import type { JobOffer } from './JobDetail';

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
    
    // 1. Récupération langue + traduction
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
        <div style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.7)', zIndex: 1100, 
            display: 'flex', justifyContent: 'center', alignItems: 'center',
            backdropFilter: 'blur(4px)'
        }} onClick={onClose}>
            
            <div style={{
                backgroundColor: 'var(--nb-bg)', 
                color: 'var(--nb-fg)',
                width: '90%', maxWidth: '700px',
                maxHeight: '90vh', overflowY: 'auto',
                borderRadius: '12px', padding: '2rem',
                boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
                position: 'relative',
                border: '1px solid var(--nb-border)'
            }} onClick={e => e.stopPropagation()}>

                {/* Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem', alignItems: 'center' }}>
                    <h2 style={{ margin: 0, fontSize: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        {/* ICI : On utilise la clé propre définie à l'étape 1 */}
                        <span>⚡</span> {t('analysis.title')}
                    </h2>
                    <button onClick={onClose} className="nb-btn-secondary" style={{ padding: '0.5rem', lineHeight: 1, minWidth: 'auto' }}>✕</button>
                </div>

                <div style={{ marginBottom: '1rem', opacity: 0.8, fontSize: '0.9rem' }}>
                   Ref: {job.intitule}
                </div>

                {loading ? (
                    <div style={{ textAlign: 'center', padding: '3rem' }}>
                        <div className="spinner" style={{ 
                            width: '40px', height: '40px', border: '4px solid #f3f3f3', 
                            borderTop: '4px solid var(--nb-accent)', borderRadius: '50%', 
                            margin: '0 auto 1rem', animation: 'spin 1s linear infinite' 
                        }}></div>
                        <p>{t('analysis.loading')}</p>
                        <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
                    </div>
                ) : error ? (
                    <div style={{ color: '#EF4444', textAlign: 'center', padding: '2rem', border: '1px dashed #EF4444', borderRadius: '8px' }}>
                        <p>{error}</p>
                    </div>
                ) : analysis ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                        
                        {/* Scores : Utilisation des clés analysis.technical et analysis.culture */}
                        <div style={{ display: 'flex', justifyContent: 'space-around', flexWrap: 'wrap', gap: '1rem' }}>
                            <ScoreCircle label={t('analysis.technical')} score={analysis.score_technique} color={getScoreColor(analysis.score_technique)} />
                            <ScoreCircle label={t('analysis.culture')} score={analysis.score_culturel} color={getScoreColor(analysis.score_culturel)} />
                        </div>

                        {/* Verdict */}
                        <div style={{ 
                            backgroundColor: 'rgba(var(--nb-accent-rgb), 0.1)', 
                            borderLeft: '4px solid var(--nb-accent)', 
                            padding: '1rem', borderRadius: '0 8px 8px 0',
                            fontStyle: 'italic', fontSize: '1.1rem'
                        }}>
                            "{analysis.verdict}"
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '2rem' }}>
                            {/* Points Forts */}
                            <div>
                                <h3 style={{ color: '#10B981', borderBottom: '1px solid #10B981', paddingBottom: '0.5rem', marginTop: 0 }}>
                                     {t('analysis.strengths')}
                                </h3>
                                <ul style={{ listStyle: 'none', padding: 0 }}>
                                    {analysis.match_reasons.map((reason, idx) => (
                                        <li key={idx} style={{ marginBottom: '0.5rem', display: 'flex', gap: '0.5rem', alignItems: 'baseline' }}>
                                            <span style={{ color: '#10B981' }}>✓</span> <span>{reason}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>

                            {/* Points à améliorer */}
                            <div>
                                <h3 style={{ color: '#EF4444', borderBottom: '1px solid #EF4444', paddingBottom: '0.5rem', marginTop: 0 }}>
                                     {t('analysis.weaknesses')}
                                </h3>
                                <ul style={{ listStyle: 'none', padding: 0 }}>
                                    {analysis.missing_skills.map((skill, idx) => (
                                        <li key={idx} style={{ marginBottom: '0.5rem', display: 'flex', gap: '0.5rem', alignItems: 'baseline' }}>
                                            <span style={{ color: '#EF4444' }}>•</span> <span>{skill}</span>
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
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
        <div style={{
            width: '100px', height: '100px', borderRadius: '50%',
            background: `conic-gradient(${color} ${score * 3.6}deg, #e5e7eb 0deg)`,
            display: 'flex', justifyContent: 'center', alignItems: 'center',
            position: 'relative'
        }}>
            <div style={{ 
                width: '85px', height: '85px', borderRadius: '50%', 
                backgroundColor: 'var(--nb-bg)', 
                display: 'flex', justifyContent: 'center', alignItems: 'center',
                flexDirection: 'column'
            }}>
                <span style={{ fontSize: '1.5rem', fontWeight: 'bold', color: color }}>{score}%</span>
            </div>
        </div>
        <span style={{ fontWeight: 600, textAlign: 'center' }}>{label}</span>
    </div>
);

export default JobMatchAnalysis;