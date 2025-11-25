import React, { useEffect, useState } from "react";
import { useAuth } from "../contexts/useAuth";

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
    const { user, signOut } = useAuth();
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

    return (
        <div className="nb-header">
            <div className="nb-header-content">
                <h2 style={{ margin: 0 }}>Dux</h2>
                <div className="nb-row nb-gap-sm">
                    <div className="nb-theme-selector">
                        <button
                            onClick={() => handleThemeChange('light')}
                            className={`nb-theme-btn ${theme === 'light' ? 'nb-theme-btn--active' : ''}`}
                            title="Light mode"
                        >
                            <SunIcon />
                        </button>
                        <button
                            onClick={() => handleThemeChange('auto')}
                            className={`nb-theme-btn ${theme === 'auto' ? 'nb-theme-btn--active' : ''}`}
                            title="Auto (system)"
                        >
                            <AutoIcon />
                        </button>
                        <button
                            onClick={() => handleThemeChange('dark')}
                            className={`nb-theme-btn ${theme === 'dark' ? 'nb-theme-btn--active' : ''}`}
                            title="Dark mode"
                        >
                            <MoonIcon />
                        </button>
                    </div>
                    {user && (
                        <button onClick={signOut} className="nb-logout-btn" title="Logout">
                            <LogoutIcon />
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Header;
