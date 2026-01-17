import React, { useState, useEffect } from "react";
import { useLanguage } from "../contexts/useLanguage";
import { useAuth } from "../contexts/useAuth";

interface AccountSettingsProps {
    onUpdate?: () => void;
}

interface AuthMethods {
    hasPassword: boolean;
    hasPasskey: boolean;
    hasLinkedIn: boolean;
}

const AccountSettings: React.FC<AccountSettingsProps> = ({ onUpdate }) => {
    const { t } = useLanguage();
    const { registerPasskey, user, checkAuth } = useAuth();
    const [authMethods, setAuthMethods] = useState<AuthMethods>({
        hasPassword: false,
        hasPasskey: false,
        hasLinkedIn: false
    });
    const [isLoading, setIsLoading] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
    const [showPasswordModal, setShowPasswordModal] = useState(false);
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');

    useEffect(() => {
        fetchAuthMethods();
    }, []);

    const fetchAuthMethods = async () => {
        try {
            const response = await fetch('/auth/methods', {
                credentials: 'include'
            });
            if (response.ok) {
                const data = await response.json();
                setAuthMethods(data);
            }
        } catch (error) {
            // Silently fail - auth methods are optional
        }
    };

    const handleLinkLinkedIn = async () => {
        setIsLoading(true);
        setMessage(null);

        try {
            const response = await fetch('/auth/linkedin/link', {
                method: 'GET',
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error(t('errors.failed_linkedin_link'));
            }

            const data = await response.json();

            const width = 600;
            const height = 700;
            const left = window.screen.width / 2 - width / 2;
            const top = window.screen.height / 2 - height / 2;

            const popup = window.open(
                data.authorization_url,
                'Link LinkedIn',
                `width=${width},height=${height},left=${left},top=${top}`
            );

            const handleMessage = (event: MessageEvent) => {
                if (event.origin !== window.location.origin) return;

                if (event.data.type === 'linkedin-oauth-success') {
                    setMessage({ type: 'success', text: t('settings.linkedin_linked') });
                    setIsLoading(false);
                    popup?.close();
                    window.removeEventListener('message', handleMessage);
                    fetchAuthMethods();
                    checkAuth();
                    if (onUpdate) onUpdate();
                } else if (event.data.type === 'linkedin-oauth-error') {
                    setMessage({ type: 'error', text: event.data.error || t('settings.linkedin_link_failed') });
                    setIsLoading(false);
                    popup?.close();
                    window.removeEventListener('message', handleMessage);
                }
            };

            window.addEventListener('message', handleMessage);

            if (!popup || popup.closed) {
                setMessage({ type: 'error', text: t('common.popup_blocked') });
                setIsLoading(false);
                window.removeEventListener('message', handleMessage);
            }
        } catch {
            setMessage({ type: 'error', text: t('settings.linkedin_link_failed') });
            setIsLoading(false);
        }
    };

    const handleAddPasskey = async () => {
        setIsLoading(true);
        setMessage(null);

        try {
            if (!user?.username) {
                throw new Error('User not found');
            }
            await registerPasskey(user.username);
            setMessage({ type: 'success', text: t('settings.passkey_added') });
            fetchAuthMethods();
            if (onUpdate) onUpdate();
        } catch {
            setMessage({ type: 'error', text: t('settings.passkey_add_failed') });
        } finally {
            setIsLoading(false);
        }
    };

    const handleSetupPassword = async () => {
        setMessage(null);

        if (newPassword !== confirmPassword) {
            setMessage({ type: 'error', text: t('settings.passwords_dont_match') });
            return;
        }

        if (newPassword.length < 12) {
            setMessage({ type: 'error', text: t('settings.password_too_short') });
            return;
        }

        setIsLoading(true);

        try {
            const response = await fetch('/auth/password/setup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ password: newPassword })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Failed to set password' }));
                throw new Error(errorData.detail);
            }

            setMessage({ type: 'success', text: t('settings.password_set') });
            setShowPasswordModal(false);
            setNewPassword('');
            setConfirmPassword('');
            fetchAuthMethods();
            if (onUpdate) onUpdate();
        } catch (error) {
            setMessage({
                type: 'error',
                text: error instanceof Error ? error.message : t('settings.password_set_failed')
            });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="nb-card home-card account-settings-card">
            <h2 style={{ margin: '0 0 1rem 0' }}>{t('settings.auth_methods')}</h2>
            <p className="nb-text-dim" style={{ marginBottom: '1.5rem' }}>
                {t('settings.auth_methods_desc')}
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {/* Password */}
                <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '1rem',
                    border: '2px solid var(--border-color)',
                    borderRadius: '4px'
                }}>
                    <div>
                        <strong>{t('auth.password')}</strong>
                        <div className="nb-text-dim" style={{ fontSize: '0.875rem' }}>
                            {authMethods.hasPassword ? t('settings.configured') : t('settings.not_configured')}
                        </div>
                    </div>
                    {authMethods.hasPassword ? (
                        <span style={{ color: 'var(--success-text, #155724)' }}>✓</span>
                    ) : (
                        <button
                            className="nb-btn nb-btn--secondary"
                            onClick={() => setShowPasswordModal(true)}
                            disabled={isLoading}
                        >
                            {t('settings.setup_password')}
                        </button>
                    )}
                </div>

                {/* Passkey */}
                <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '1rem',
                    border: '2px solid var(--border-color)',
                    borderRadius: '4px'
                }}>
                    <div>
                        <strong>{t('auth.passkey')}</strong>
                        <div className="nb-text-dim" style={{ fontSize: '0.875rem' }}>
                            {authMethods.hasPasskey ? t('settings.configured') : t('settings.not_configured')}
                        </div>
                    </div>
                    {authMethods.hasPasskey ? (
                        <span style={{ color: 'var(--success-text, #155724)' }}>✓</span>
                    ) : (
                        <button
                            className="nb-btn nb-btn--secondary"
                            onClick={handleAddPasskey}
                            disabled={isLoading}
                        >
                            {t('settings.add_passkey')}
                        </button>
                    )}
                </div>

                {/* LinkedIn */}
                <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '1rem',
                    border: '2px solid var(--border-color)',
                    borderRadius: '4px'
                }}>
                    <div>
                        <strong>LinkedIn</strong>
                        <div className="nb-text-dim" style={{ fontSize: '0.875rem' }}>
                            {authMethods.hasLinkedIn ? t('settings.configured') : t('settings.not_configured')}
                        </div>
                    </div>
                    {authMethods.hasLinkedIn ? (
                        <span style={{ color: 'var(--success-text, #155724)' }}>✓</span>
                    ) : (
                        <button
                            className="nb-btn nb-btn--secondary"
                            onClick={handleLinkLinkedIn}
                            disabled={isLoading}
                        >
                            {t('settings.link_linkedin')}
                        </button>
                    )}
                </div>
            </div>

            {message && (
                <div style={{
                    marginTop: '1rem',
                    padding: '0.75rem',
                    backgroundColor: message.type === 'success' ? 'var(--success-bg, #d4edda)' : 'var(--error-bg, #f8d7da)',
                    color: message.type === 'success' ? 'var(--success-text, #155724)' : 'var(--error-text, #721c24)',
                    borderRadius: '4px',
                    fontSize: '0.875rem'
                }}>
                    {message.text}
                </div>
            )}

            {/* Password Setup Modal */}
            {showPasswordModal && (
                <div style={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    backgroundColor: 'rgba(0, 0, 0, 0.5)',
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    zIndex: 1000
                }}>
                    <div className="nb-card" style={{
                        maxWidth: '400px',
                        width: '90%',
                        margin: '1rem'
                    }}>
                        <h3 style={{ marginTop: 0 }}>{t('settings.setup_password')}</h3>
                        <p className="nb-text-dim" style={{ fontSize: '0.875rem' }}>
                            {t('settings.password_requirements')}
                        </p>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                            <input
                                className="nb-input"
                                type="password"
                                placeholder={t('settings.new_password')}
                                value={newPassword}
                                onChange={(e) => setNewPassword(e.target.value)}
                                disabled={isLoading}
                            />
                            <input
                                className="nb-input"
                                type="password"
                                placeholder={t('settings.confirm_password')}
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                disabled={isLoading}
                            />

                            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
                                <button
                                    className="nb-btn nb-btn--accent"
                                    onClick={handleSetupPassword}
                                    disabled={isLoading || !newPassword || !confirmPassword}
                                    style={{ flex: 1 }}
                                >
                                    {isLoading ? t('settings.setting_up') : t('settings.setup')}
                                </button>
                                <button
                                    className="nb-btn nb-btn--ghost"
                                    onClick={() => {
                                        setShowPasswordModal(false);
                                        setNewPassword('');
                                        setConfirmPassword('');
                                        setMessage(null);
                                    }}
                                    disabled={isLoading}
                                    style={{ flex: 1 }}
                                >
                                    {t('settings.cancel')}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}; export default AccountSettings;
