import React, { useState } from "react";
import { useAuth } from "./contexts/useAuth";
import { useLanguage } from "./contexts/useLanguage";
import Header from "./components/Header";

const AuthPage: React.FC = () => {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [mode, setMode] = useState<"password" | "passkey">("password");
    const [isRegistering, setIsRegistering] = useState(false);

    const { signIn, signUp, signInWithPasskey, registerPasskey, loading, error, clearError } = useAuth();
    const { t } = useLanguage();

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

                {error && <div className="nb-alert nb-alert--danger nb-mt">{error}</div>}
            </div>
        </>
    );
};

export default AuthPage;
