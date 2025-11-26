import React from "react";
import { useAuth } from "./contexts/useAuth";
import { useLanguage } from "./contexts/useLanguage";
import { Header, AccountSettings, PreferencesCard } from "./components";

const Settings: React.FC = () => {
    const { checkAuth } = useAuth();
    const { t } = useLanguage();

    return (
        <>
            <Header />
            <div className="nb-page nb-stack">
                <div className="nb-card">
                    <h1 style={{ margin: '0 0 1rem 0' }}>{t('settings.page_title')}</h1>
                    <p className="nb-text-dim">{t('settings.page_description')}</p>
                </div>
                <AccountSettings onUpdate={checkAuth} />
                <PreferencesCard />
            </div>
        </>
    );
};

export default Settings;
