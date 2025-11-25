import React from "react";
import { useAuth } from "./contexts/useAuth";
import { useLanguage } from "./contexts/useLanguage";
import { Header, AccountCard } from "./components";

const Home: React.FC = () => {
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
                </div>
            </div>
        </>
    );
};

export default Home;
