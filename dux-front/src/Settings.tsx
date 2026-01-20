import React from "react";
import { useAuth } from "./contexts/useAuth";
import { useLanguage } from "./contexts/useLanguage";
import { Header, AccountSettings, PreferencesCard, DebugCard } from "./components";
import "./styles/home.css";

const Settings: React.FC = () => {
    const { checkAuth } = useAuth();
    const { t } = useLanguage();
    const version = import.meta.env.VITE_APP_VERSION || import.meta.env.VITE_GIT_TAG || "dev";

    return (
        <>
            <Header />
            <main className="nb-page home-container">
                <div style={{ padding: 'clamp(1rem, 5vw, 2rem)', paddingBottom: '0' }}>
                    <h1 style={{ margin: '0 0 0.5rem 0' }}>{t('settings.page_title')}</h1>
                    <p className="nb-text-dim">{t('settings.page_description')}</p>
                </div>
                <div className="home-grid">
                    <AccountSettings onUpdate={checkAuth} />
                    <PreferencesCard />
                    <DebugCard />
                </div>
                <div className="home-version">Version {version}</div>
            </main>
        </>
    );
};

export default Settings;
