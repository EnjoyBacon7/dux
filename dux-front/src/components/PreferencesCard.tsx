import React, { useEffect, useState } from "react";
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

const applyTheme = (selectedTheme: 'light' | 'dark' | 'auto') => {
    const root = document.documentElement;

    if (selectedTheme === 'auto') {
        root.removeAttribute('data-theme');
    } else {
        root.setAttribute('data-theme', selectedTheme);
    }
};

const PreferencesCard: React.FC = () => {
    const { language, setLanguage, t } = useLanguage();
    const [theme, setTheme] = useState<'light' | 'dark' | 'auto'>(() => {
        return localStorage.getItem('theme') as 'light' | 'dark' | 'auto' || 'auto';
    });
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);
    const [deleteError, setDeleteError] = useState<string | null>(null);

    useEffect(() => {
        applyTheme(theme);
    }, [theme]);

    const handleThemeChange = (newTheme: 'light' | 'dark' | 'auto') => {
        setTheme(newTheme);
        localStorage.setItem('theme', newTheme);
        applyTheme(newTheme);
    };

    const handleDeleteAccount = async () => {
        setIsDeleting(true);
        setDeleteError(null);

        try {
            const response = await fetch('/auth/account', {
                method: 'DELETE',
                credentials: 'include'
            });

            if (response.ok) {
                // Account deleted successfully, clear state and redirect
                window.location.href = '/login';
            } else {
                const data = await response.json();
                setDeleteError(data.detail || 'Failed to delete account');
            }
        } catch (error) {
            setDeleteError('An error occurred while deleting your account');
            console.error('Delete account error:', error);
        } finally {
            setIsDeleting(false);
        }
    };

    const languages: Array<{ code: 'en' | 'es' | 'fr' | 'de' | 'pt' | 'la' | 'auto'; label: string }> = [
        { code: 'auto', label: 'Auto' },
        { code: 'en', label: 'EN' },
        { code: 'es', label: 'ES' },
        { code: 'fr', label: 'FR' },
        { code: 'de', label: 'DE' },
        { code: 'pt', label: 'PT' },
        { code: 'la', label: 'LA' },
    ];

    return (
        <div className="nb-card">
            <h2 style={{ marginTop: 0 }}>{t('preferences.title')}</h2>

            {/* Language Setting */}
            <div style={{ marginBottom: '1.5rem' }}>
                <h3 style={{ marginBottom: '0.5rem', fontSize: '1rem' }}>{t('preferences.language')}</h3>
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
            </div>

            {/* Theme Setting */}
            <div>
                <h3 style={{ marginBottom: '0.5rem', fontSize: '1rem' }}>{t('preferences.theme')}</h3>
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
            </div>

            {/* Delete Account Section */}
            <div style={{ marginTop: '2rem', paddingTop: '1.5rem', borderTop: '2px solid var(--nb-border)' }}>
                <h3 style={{ marginBottom: '0.5rem', fontSize: '1rem', color: 'var(--nb-error)' }}>
                    {t('preferences.danger_zone')}
                </h3>
                <p style={{ fontSize: '0.875rem', color: 'var(--nb-text-dim)', marginBottom: '1rem' }}>
                    {t('preferences.delete_warning')}
                </p>
                <button
                    onClick={() => setShowDeleteModal(true)}
                    className="nb-btn nb-btn--danger"
                >
                    {t('preferences.delete_account')}
                </button>
            </div>

            {/* Delete Confirmation Modal */}
            {showDeleteModal && (
                <div style={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    backgroundColor: 'rgba(0, 0, 0, 0.5)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    zIndex: 1000
                }}>
                    <div className="nb-card" style={{
                        maxWidth: '500px',
                        margin: '1rem',
                        position: 'relative'
                    }}>
                        <h2 style={{ marginTop: 0, color: 'var(--nb-error)' }}>
                            {t('preferences.confirm_delete')}
                        </h2>
                        <p style={{ marginBottom: '1rem' }}>
                            {t('preferences.confirm_delete_message')}
                        </p>

                        {deleteError && (
                            <div style={{
                                padding: '0.75rem',
                                backgroundColor: 'var(--nb-error-bg)',
                                border: '2px solid var(--nb-error)',
                                marginBottom: '1rem',
                                color: 'var(--nb-error)'
                            }}>
                                {deleteError}
                            </div>
                        )}

                        <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
                            <button
                                onClick={() => {
                                    setShowDeleteModal(false);
                                    setDeleteError(null);
                                }}
                                className="nb-btn nb-btn-outline"
                                disabled={isDeleting}
                            >
                                {t('common.cancel')}
                            </button>
                            <button
                                onClick={handleDeleteAccount}
                                className="nb-btn nb-btn--danger"
                                disabled={isDeleting}
                            >
                                {isDeleting ? t('common.deleting') : t('preferences.delete_permanently')}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default PreferencesCard;
