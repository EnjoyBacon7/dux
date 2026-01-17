import React from "react";
import { useNavigate } from "react-router-dom";
import { useLanguage } from "../contexts/useLanguage";

const WelcomeCard: React.FC = () => {
    const navigate = useNavigate();
    const { t } = useLanguage();

    return (
        <div className="nb-card home-card">
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
