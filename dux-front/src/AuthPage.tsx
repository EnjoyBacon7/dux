import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./contexts/useAuth";
import { useLanguage } from "./contexts/useLanguage";
import { Header } from "./components";

const AuthPage: React.FC = () => {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [mode, setMode] = useState<"password" | "passkey">("password");
    const [isRegistering, setIsRegistering] = useState(false);
    const [isLinkedInLoading, setIsLinkedInLoading] = useState(false);
    const [notification, setNotification] = useState<{ type: 'success' | 'error', text: string } | null>(null);

    const { signIn, signUp, signInWithPasskey, registerPasskey, loading, error, clearError, user, checkAuth } = useAuth();
    const { t } = useLanguage();
    const navigate = useNavigate();

    // If already logged in, redirect away from login page
    useEffect(() => {
        if (user) {
            navigate("/");
        }
    }, [user, navigate]);

    // Auto-dismiss notifications after 5 seconds
    useEffect(() => {
        if (notification) {
            const timer = setTimeout(() => setNotification(null), 5000);
            return () => clearTimeout(timer);
        }
    }, [notification]);

    const handlePasswordSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        clearError();

        try {
            if (isRegistering) {
                await signUp(username, password);
                setNotification({ type: 'success', text: t('auth.registration_successful') });
                setIsRegistering(false);
                setPassword("");
            } else {
                await signIn(username, password);
            }
        } catch {
            // Error is handled by context
        }
    };

    const handlePasskeyLogin = async () => {
        clearError();
        try {
            await signInWithPasskey(username);
        } catch {
            // Error is handled by context
        }
    };

    const handlePasskeyRegister = async () => {
        clearError();
        try {
            await registerPasskey(username);
            setNotification({ type: 'success', text: t('auth.passkey_registered_success') });
        } catch {
            // Error is handled by context
        }
    };

    const handleLinkedInSignIn = async () => {
        setIsLinkedInLoading(true);
        clearError();

        try {
            // Request authorization URL from backend
            const response = await fetch('/auth/linkedin/authorize', {
                method: 'GET',
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error('Failed to initiate LinkedIn sign-in');
            }

            const data = await response.json();

            // Open LinkedIn OAuth in a popup window
            const width = 600;
            const height = 700;
            const left = window.screen.width / 2 - width / 2;
            const top = window.screen.height / 2 - height / 2;

            const popup = window.open(
                data.authorization_url,
                'LinkedIn Sign In',
                `width=${width},height=${height},left=${left},top=${top}`
            );

            // Listen for OAuth callback
            const handleMessage = (event: MessageEvent) => {
                if (event.origin !== window.location.origin) return;

                if (event.data.type === 'linkedin-oauth-success') {
                    setIsLinkedInLoading(false);
                    popup?.close();
                    window.removeEventListener('message', handleMessage);

                    // Refresh auth state and navigate to home
                    checkAuth();
                    navigate('/');
                } else if (event.data.type === 'linkedin-oauth-error') {
                    setIsLinkedInLoading(false);
                    popup?.close();
                    window.removeEventListener('message', handleMessage);
                    setNotification({ type: 'error', text: event.data.error || t('errors.linkedin_signin_failed') });
                }
            };

            window.addEventListener('message', handleMessage);

            // Check if popup was blocked
            if (!popup || popup.closed) {
                setIsLinkedInLoading(false);
                window.removeEventListener('message', handleMessage);
                setNotification({ type: 'error', text: t('common.popup_blocked_site') });
            }
        } catch {
            setIsLinkedInLoading(false);
            setNotification({ type: 'error', text: t('errors.linkedin_signin_initiate_failed') });
        }
    };

    return (
        <div style={{
            height: '100vh',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column'
        }}>
            <Header />
            <div style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'flex-start',
                padding: '2rem',
                position: 'relative',
                overflow: 'hidden',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
            }}>
                {/* Animated Background Shapes */}
                <div style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    zIndex: 0,
                    pointerEvents: 'none'
                }}>
                    {/* Spiral 1 */}
                    <div style={{
                        position: 'absolute',
                        top: '10%',
                        left: '60%',
                        width: '300px',
                        height: '300px',
                        border: '3px solid rgba(255, 255, 255, 0.2)',
                        borderRadius: '50% 40% 60% 40%',
                        animation: 'spin 20s linear infinite',
                    }} />
                    {/* Spiral 2 */}
                    <div style={{
                        position: 'absolute',
                        top: '50%',
                        right: '15%',
                        width: '200px',
                        height: '200px',
                        border: '3px solid rgba(255, 255, 255, 0.15)',
                        borderRadius: '60% 40% 40% 60%',
                        animation: 'spin 15s linear infinite reverse',
                    }} />
                    {/* Spiral 3 */}
                    <div style={{
                        position: 'absolute',
                        bottom: '15%',
                        left: '50%',
                        width: '250px',
                        height: '250px',
                        border: '3px solid rgba(255, 255, 255, 0.18)',
                        borderRadius: '40% 60% 50% 40%',
                        animation: 'spin 25s linear infinite',
                    }} />
                    {/* Additional decorative circles */}
                    <div style={{
                        position: 'absolute',
                        top: '30%',
                        right: '5%',
                        width: '150px',
                        height: '150px',
                        background: 'radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%)',
                        borderRadius: '50%',
                        animation: 'pulse 8s ease-in-out infinite',
                    }} />
                    <div style={{
                        position: 'absolute',
                        bottom: '25%',
                        right: '40%',
                        width: '180px',
                        height: '180px',
                        background: 'radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%)',
                        borderRadius: '50%',
                        animation: 'pulse 10s ease-in-out infinite 2s',
                    }} />
                </div>

                {/* Login Card */}
                <div className="nb-card" style={{
                    maxWidth: '450px',
                    width: '100%',
                    marginLeft: '5%',
                    position: 'relative',
                    zIndex: 1
                }}>
                    <h1 className="nb-center" style={{ marginTop: 0 }}>{t('auth.title')}</h1>

                    <div className="nb-tabs" style={{ marginBottom: '1rem' }}>
                        <button
                            onClick={() => setMode("password")}
                            className={`nb-btn nb-tab ${mode === 'password' ? 'nb-btn--accent' : 'nb-btn--ghost'}`}
                            type="button"
                        >{t('auth.password')}</button>
                        <button
                            onClick={() => setMode("passkey")}
                            className={`nb-btn nb-tab ${mode === 'passkey' ? 'nb-btn--accent' : 'nb-btn--ghost'}`}
                            type="button"
                        >{t('auth.passkey')}</button>
                    </div>

                    {mode === "password" ? (
                        <form className="nb-form" onSubmit={handlePasswordSubmit}>
                            <input
                                className="nb-input"
                                type="text"
                                placeholder={t('auth.username')}
                                value={username}
                                onChange={e => setUsername(e.target.value.trim())}
                                required
                            />
                            <input
                                className="nb-input"
                                type="password"
                                placeholder={t('auth.password.placeholder')}
                                value={password}
                                onChange={e => setPassword(e.target.value)}
                                required
                            />
                            <button
                                type="submit"
                                disabled={loading}
                                className={`nb-btn ${loading ? 'nb-btn--ghost' : 'nb-btn--accent'}`}
                            >{loading ? (isRegistering ? t('auth.registering') : t('auth.logging_in')) : (isRegistering ? t('auth.register') : t('auth.login'))}</button>
                            <button
                                type="button"
                                onClick={() => { setIsRegistering(!isRegistering); clearError(); }}
                                className="nb-btn nb-btn--ghost"
                            >{isRegistering ? t('auth.already_account') : t('auth.need_account')}</button>
                        </form>
                    ) : (
                        <div className="nb-form">
                            <input
                                className="nb-input"
                                type="text"
                                placeholder={t('auth.username')}
                                value={username}
                                onChange={e => setUsername(e.target.value.trim())}
                                required
                            />
                            <button
                                onClick={handlePasskeyLogin}
                                disabled={loading || !username}
                                className={`nb-btn ${loading || !username ? 'nb-btn--ghost' : 'nb-btn--accent'}`}
                                type="button"
                            >{loading ? t('auth.authenticating') : t('auth.passkey.login')}</button>
                            <button
                                onClick={handlePasskeyRegister}
                                disabled={loading || !username}
                                className={`nb-btn ${loading || !username ? 'nb-btn--ghost' : 'nb-btn--success'}`}
                                type="button"
                            >{loading ? t('auth.registering') : t('auth.passkey.register')}</button>
                        </div>
                    )}

                    <div style={{ margin: '1.5rem 0', textAlign: 'center', position: 'relative' }}>
                        <hr style={{ border: 'none', borderTop: '1px solid var(--border-color)', margin: '1rem 0' }} />
                        <span style={{
                            position: 'absolute',
                            top: '50%',
                            left: '50%',
                            transform: 'translate(-50%, -50%)',
                            background: 'var(--bg-color)',
                            padding: '0 1rem',
                            color: 'var(--text-dim)'
                        }}>{t('auth.or')}</span>
                    </div>

                    <button
                        onClick={handleLinkedInSignIn}
                        disabled={isLinkedInLoading}
                        className="nb-btn nb-btn--secondary"
                        type="button"
                        style={{ width: '100%' }}
                    >
                        {isLinkedInLoading ? t('linkedin.connecting') : t('auth.linkedin_signin')}
                    </button>

                    <p style={{ textAlign: 'center', marginTop: '1rem', fontSize: '0.875rem', color: 'var(--text-dim)' }}>
                        {t('privacy.by_using')}{' '}
                        <a href="/privacy" target="_blank" style={{ color: 'var(--accent-color)' }}>
                            {t('privacy.title')}
                        </a>
                    </p>

                    {error && <div className="nb-alert nb-alert--danger nb-mt">{error}</div>}

                    {notification && (
                        <div style={{
                            marginTop: '1rem',
                            padding: '0.75rem',
                            backgroundColor: notification.type === 'success' ? 'var(--success-bg, #d4edda)' : 'var(--error-bg, #f8d7da)',
                            color: notification.type === 'success' ? 'var(--success-text, #155724)' : 'var(--error-text, #721c24)',
                            borderRadius: '4px',
                            fontSize: '0.875rem',
                            animation: 'fadeOut 0.5s ease-out 4.5s forwards'
                        }}>
                            {notification.text}
                        </div>
                    )}
                </div>
            </div>

            {/* Add CSS animations */}
            <style>{`
                @keyframes spin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
                @keyframes pulse {
                    0%, 100% { 
                        transform: scale(1);
                        opacity: 0.5;
                    }
                    50% { 
                        transform: scale(1.1);
                        opacity: 0.8;
                    }
                }
                @keyframes fadeOut {
                    from { opacity: 1; }
                    to { opacity: 0; }
                }
            `}</style>
        </div>
    );
};

export default AuthPage;
