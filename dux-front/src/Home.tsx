import React from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./contexts/useAuth";
import { useLanguage } from "./contexts/useLanguage";
import { Header, AccountCard } from "./components";

const Home: React.FC = () => {
    const navigate = useNavigate();
    const { user } = useAuth();
    const { t } = useLanguage();
    if (!user) return null; // Guard: page is wrapped by RequireAuth

    return (
        <>
            <Header />
            <div className="nb-page nb-stack">
                <AccountCard
                    username={user.username}
                    firstName={user.first_name}
                    lastName={user.last_name}
                    title={user.title}
                    profilePicture={user.profile_picture}
                />
                <div className="nb-card">
                    <h1 style={{ margin: '0 0 1rem 0' }}>{t('home.welcome')}</h1>
                    <p className="nb-text-dim">{t('home.authenticated')}</p>
                    <div style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                        <button 
                            onClick={() => navigate('/jobs')}
                            className="nb-btn"
                        >
                            {t('jobs.title')}
                        </button>
                    </div>
                </div>
            </div>
        </>
    );
};

export default Home;
