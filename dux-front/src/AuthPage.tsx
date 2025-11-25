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

    const { signIn, signUp, signInWithPasskey, registerPasskey, loading, error, clearError, user, checkAuth } = useAuth();
    const { t } = useLanguage();
    const navigate = useNavigate();

    // If already logged in, redirect away from login page
    useEffect(() => {
        if (user) {
            navigate("/");
        }
    }, [user, navigate]);

    const handlePasswordSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        clearError();

        try {
            if (isRegistering) {
                await signUp(username, password);
                alert("Registration successful! You can now log in.");
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
            alert("Passkey registered successfully! You can now log in.");
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
                    alert(event.data.error || 'Failed to sign in with LinkedIn');
                }
            };

            window.addEventListener('message', handleMessage);

            // Check if popup was blocked
            if (!popup || popup.closed) {
                setIsLinkedInLoading(false);
                window.removeEventListener('message', handleMessage);
                alert('Popup blocked. Please allow popups for this site.');
            }
        } catch {
            setIsLinkedInLoading(false);
            alert('Failed to initiate LinkedIn sign-in');
        }
    };

    return (
        <>
            <Header />
            <div className="nb-page nb-card">
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
            </div>
        </>
    );
};

export default AuthPage;
