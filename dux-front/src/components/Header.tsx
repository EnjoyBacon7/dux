import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/useAuth";
import { useLanguage } from "../contexts/useLanguage";

const SunIcon = () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="square" strokeLinejoin="miter">
        <circle cx="12" cy="12" r="4" />
        <line x1="12" y1="1" x2="12" y2="3" />
        <line x1="12" y1="21" x2="12" y2="23" />
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
        <line x1="1" y1="12" x2="3" y2="12" />
        <line x1="21" y1="12" x2="23" y2="12" />
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
    </svg>
);

const MoonIcon = () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="square" strokeLinejoin="miter">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
);

const AutoIcon = () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="square" strokeLinejoin="miter">
        <rect x="2" y="3" width="20" height="14" rx="2" />
        <line x1="8" y1="21" x2="16" y2="21" />
        <line x1="12" y1="17" x2="12" y2="21" />
    </svg>
);

const LogoutIcon = () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="square" strokeLinejoin="miter">
        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
        <polyline points="16 17 21 12 16 7" />
        <line x1="21" y1="12" x2="9" y2="12" />
    </svg>
);

const applyTheme = (selectedTheme: 'light' | 'dark' | 'auto') => {
    const root = document.documentElement;

    if (selectedTheme === 'auto') {
        root.removeAttribute('data-theme');
    } else {
        root.setAttribute('data-theme', selectedTheme);
    }
};

const Header: React.FC = () => {
    const navigate = useNavigate();
    const { user, signOut } = useAuth();
    const { language, setLanguage, t } = useLanguage();
    const [theme, setTheme] = useState<'light' | 'dark' | 'auto'>(() => {
        return localStorage.getItem('theme') as 'light' | 'dark' | 'auto' || 'auto';
    });

    useEffect(() => {
        applyTheme(theme);
    }, [theme]);

    const handleThemeChange = (newTheme: 'light' | 'dark' | 'auto') => {
        setTheme(newTheme);
        localStorage.setItem('theme', newTheme);
        applyTheme(newTheme);
    };

    const languages: Array<{ code: 'en' | 'es' | 'fr' | 'de' | 'pt' | 'auto'; label: string }> = [
        { code: 'auto', label: 'Auto' },
        { code: 'en', label: 'EN' },
        { code: 'es', label: 'ES' },
        { code: 'fr', label: 'FR' },
        { code: 'de', label: 'DE' },
        { code: 'pt', label: 'PT' },
    ];

    return (
        <div className="nb-header">
            <div className="nb-header-content">
                <button
                    onClick={() => navigate('/')}
                    style={{
                        margin: 0,
                        background: 'none',
                        border: 'none',
                        padding: 0,
                        cursor: 'pointer',
                        font: 'inherit',
                        color: 'inherit'
                    }}
                >
                    <h2 style={{ margin: 0 }}>{t('app.name')}</h2>
                </button>
                <div className="nb-row nb-gap-sm">
                    {/* Language Selector */}
                    <div className="nb-theme-selector">
                        {languages.map((lang) => (
                            <button
                                key={lang.code}
                                onClick={() => setLanguage(lang.code)}
                                className={`nb-theme-btn ${language === lang.code ? 'nb-theme-btn--active' : ''}`}
                                title={lang.code === 'auto' ? t('language.auto') : lang.label}
                            >
                                {lang.label}
                            </button>
                        ))}
                    </div>
                    {/* Theme Selector */}
                    <div className="nb-theme-selector">
                        <button
                            onClick={() => handleThemeChange('light')}
                            className={`nb-theme-btn ${theme === 'light' ? 'nb-theme-btn--active' : ''}`}
                            title={t('theme.light')}
                        >
                            <SunIcon />
                        </button>
                        <button
                            onClick={() => handleThemeChange('auto')}
                            className={`nb-theme-btn ${theme === 'auto' ? 'nb-theme-btn--active' : ''}`}
                            title={t('theme.auto')}
                        >
                            <AutoIcon />
                        </button>
                        <button
                            onClick={() => handleThemeChange('dark')}
                            className={`nb-theme-btn ${theme === 'dark' ? 'nb-theme-btn--active' : ''}`}
                            title={t('theme.dark')}
                        >
                            <MoonIcon />
                        </button>
                    </div>
                    {user && (
                        <button onClick={signOut} className="nb-logout-btn" title={t('header.logout')}>
                            <LogoutIcon />
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Header;
