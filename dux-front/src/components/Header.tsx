import React, { useState, useRef, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/useAuth";
import { useLanguage } from "../contexts/useLanguage";

const SettingsIcon = () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="square" strokeLinejoin="miter">
        <circle cx="12" cy="12" r="3" />
        <path d="M12 1v6m0 6v6M5.64 5.64l4.24 4.24m4.24 4.24l4.24 4.24M1 12h6m6 0h6M5.64 18.36l4.24-4.24m4.24-4.24l4.24-4.24" />
    </svg>
);

const LogoutIcon = () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="square" strokeLinejoin="miter">
        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
        <polyline points="16 17 21 12 16 7" />
        <line x1="21" y1="12" x2="9" y2="12" />
    </svg>
);

const Header: React.FC = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const { user, signOut } = useAuth();
    const { t } = useLanguage();
    const [dropdownOpen, setDropdownOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    // Generate initials from user data
    const getInitials = () => {
        if (!user) return '';
        if (user.first_name && user.last_name) {
            return `${user.first_name[0]}${user.last_name[0]}`.toUpperCase();
        }
        if (user.first_name) {
            return user.first_name[0].toUpperCase();
        }
        return user.username.substring(0, 2).toUpperCase();
    };

    // Get breadcrumb text based on current path
    const getBreadcrumb = () => {
        const path = location.pathname;
        if (path === '/settings') {
            return t('header.settings');
        }
        return null;
    };

    const breadcrumb = getBreadcrumb();

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setDropdownOpen(false);
            }
        };

        if (dropdownOpen) {
            document.addEventListener('mousedown', handleClickOutside);
        }

        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [dropdownOpen]);

    const handleLogout = async () => {
        setDropdownOpen(false);
        await signOut();
    };

    return (
        <div className="nb-header">
            <div className="nb-header-content">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
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
                    {breadcrumb && (
                        <>
                            <span style={{
                                fontSize: '1.25rem',
                                color: 'var(--nb-fg)',
                                opacity: 0.5,
                                userSelect: 'none'
                            }}>
                                /
                            </span>
                            <span style={{
                                fontSize: '1.25rem',
                                fontWeight: 600,
                                color: 'var(--nb-fg)'
                            }}>
                                {breadcrumb}
                            </span>
                        </>
                    )}
                </div>
                <div className="nb-row nb-gap-sm">
                    {user && (
                        <div style={{ position: 'relative' }} ref={dropdownRef}>
                            <button
                                onClick={() => setDropdownOpen(!dropdownOpen)}
                                className="nb-logout-btn"
                                style={{
                                    width: '40px',
                                    height: '40px',
                                    padding: 0,
                                    borderRadius: '6px',
                                    overflow: 'hidden',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    backgroundColor: 'var(--nb-accent)',
                                    border: 'var(--nb-border) solid var(--nb-fg)'
                                }}
                                title={t('header.menu')}
                            >
                                {user.profile_picture ? (
                                    <img
                                        src={user.profile_picture}
                                        alt={user.username}
                                        style={{
                                            width: '100%',
                                            height: '100%',
                                            objectFit: 'cover'
                                        }}
                                    />
                                ) : (
                                    <div style={{
                                        width: '100%',
                                        height: '100%',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        backgroundColor: 'var(--accent-color)',
                                        color: 'white',
                                        fontWeight: 'bold',
                                        fontSize: '0.875rem'
                                    }}>
                                        {getInitials()}
                                    </div>
                                )}
                            </button>
                            {dropdownOpen && (
                                <div className="nb-card" style={{
                                    position: 'absolute',
                                    top: 'calc(100% + 0.5rem)',
                                    right: 0,
                                    minWidth: '150px',
                                    zIndex: 1000,
                                    padding: 0,
                                    margin: 0
                                }}>
                                    <button
                                        onClick={() => {
                                            setDropdownOpen(false);
                                            navigate('/settings');
                                        }}
                                        style={{
                                            width: '100%',
                                            padding: '0.75rem 1rem',
                                            border: 'none',
                                            background: 'none',
                                            textAlign: 'left',
                                            cursor: 'pointer',
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '0.5rem',
                                            color: 'var(--nb-fg)',
                                            fontSize: '0.875rem',
                                            borderRadius: '4px',
                                            transition: 'background-color 0.15s ease'
                                        }}
                                        onMouseEnter={(e) => {
                                            e.currentTarget.style.backgroundColor = 'var(--hover-bg, rgba(0, 0, 0, 0.05))';
                                        }}
                                        onMouseLeave={(e) => {
                                            e.currentTarget.style.backgroundColor = 'transparent';
                                        }}
                                    >
                                        <SettingsIcon />
                                        {t('header.settings')}
                                    </button>
                                    <button
                                        onClick={handleLogout}
                                        style={{
                                            width: '100%',
                                            padding: '0.75rem 1rem',
                                            border: 'none',
                                            background: 'none',
                                            textAlign: 'left',
                                            cursor: 'pointer',
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '0.5rem',
                                            color: 'var(--nb-fg)',
                                            fontSize: '0.875rem',
                                            borderRadius: '4px',
                                            transition: 'background-color 0.15s ease'
                                        }}
                                        onMouseEnter={(e) => {
                                            e.currentTarget.style.backgroundColor = 'var(--hover-bg, rgba(0, 0, 0, 0.05))';
                                        }}
                                        onMouseLeave={(e) => {
                                            e.currentTarget.style.backgroundColor = 'transparent';
                                        }}
                                    >
                                        <LogoutIcon />
                                        {t('header.logout')}
                                    </button>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Header;
