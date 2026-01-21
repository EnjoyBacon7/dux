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
            <p className="nb-text-dim">{t('home.authenticated')}</p>
            <div className="home-actions">
                <button
                    onClick={() => navigate('/jobs')}
                    className="nb-btn"
                >
                    {t('jobs.title')}
                </button>
            </div>
        </div>
    );
};

export default WelcomeCard;
