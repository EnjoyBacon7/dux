import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useLanguage } from "../contexts/useLanguage";
import { useAuth } from "../contexts/useAuth";

const WelcomeCard: React.FC = () => {
    const navigate = useNavigate();
    const { t } = useLanguage();
    const { user } = useAuth();
    const [isFirstLogin, setIsFirstLogin] = useState(false);

    useEffect(() => {
        if (user?.user_id) {
            const seenWelcomeKey = `welcome_card_seen_${user.user_id}`;
            const hasSeenWelcome = localStorage.getItem(seenWelcomeKey);

            if (!hasSeenWelcome) {
                setIsFirstLogin(true);
                localStorage.setItem(seenWelcomeKey, 'true');
            }
        }
    }, [user?.user_id]);

    if (!isFirstLogin) return null;

    return (
        <div className="nb-card home-card welcome-card">
            <h1 className="home-title">{t('home.welcome')}</h1>
            <p className="nb-text-dim" style={{ marginBottom: '1rem' }}>{t('home.welcome_intro')}</p>

            <div style={{
                display: 'grid',
                gap: '0.75rem',
                marginBottom: '1.5rem',
                fontSize: '0.9rem'
            }}>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
                    <span style={{ fontSize: '1.2rem', minWidth: '1.5rem' }}>📄</span>
                    <div>
                        <strong>{t('home.feature_cv_title')}</strong>
                        <p style={{ margin: '0.25rem 0 0 0', opacity: 0.8 }}>{t('home.feature_cv_desc')}</p>
                    </div>
                </div>

                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
                    <span style={{ fontSize: '1.2rem', minWidth: '1.5rem' }}>🎯</span>
                    <div>
                        <strong>{t('home.feature_jobs_title')}</strong>
                        <p style={{ margin: '0.25rem 0 0 0', opacity: 0.8 }}>{t('home.feature_jobs_desc')}</p>
                    </div>
                </div>

                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
                    <span style={{ fontSize: '1.2rem', minWidth: '1.5rem' }}>⚡</span>
                    <div>
                        <strong>{t('home.feature_analysis_title')}</strong>
                        <p style={{ margin: '0.25rem 0 0 0', opacity: 0.8 }}>{t('home.feature_analysis_desc')}</p>
                    </div>
                </div>
            </div>

            <div className="home-actions">
                <button
                    onClick={() => navigate('/jobs')}
                    className="nb-btn"
                >
                    {t('home.explore_jobs')}
                </button>
            </div>
        </div>
    );
};

export default WelcomeCard;
