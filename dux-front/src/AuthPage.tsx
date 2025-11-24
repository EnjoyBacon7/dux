import React, { useState } from "react";
import { useAuth } from "./contexts/useAuth";

const AuthPage: React.FC = () => {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [mode, setMode] = useState<"password" | "passkey">("password");
    const [isRegistering, setIsRegistering] = useState(false);

    const { signIn, signUp, signInWithPasskey, registerPasskey, loading, error, clearError } = useAuth();

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
        <div style={{ maxWidth: 400, margin: "2rem auto", padding: 24, border: "1px solid #eee", borderRadius: 8 }}>
            <h1 style={{ textAlign: "center" }}>Authentication</h1>

            <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
                <button
                    onClick={() => setMode("password")}
                    style={{
                        flex: 1,
                        padding: "8px 0",
                        background: mode === "password" ? "#1976d2" : "#eee",
                        color: mode === "password" ? "white" : "#333",
                        border: "none",
                        borderRadius: 4,
                        fontWeight: 600,
                        cursor: "pointer"
                    }}>
                    Password
                </button>
                <button
                    onClick={() => setMode("passkey")}
                    style={{
                        flex: 1,
                        padding: "8px 0",
                        background: mode === "passkey" ? "#1976d2" : "#eee",
                        color: mode === "passkey" ? "white" : "#333",
                        border: "none",
                        borderRadius: 4,
                        fontWeight: 600,
                        cursor: "pointer"
                    }}>
                    Passkey
                </button>
            </div>

            {mode === "password" ? (
                <form style={{ display: "flex", flexDirection: "column", gap: 16 }} onSubmit={handlePasswordSubmit}>
                    <input
                        type="text"
                        placeholder="Username"
                        value={username}
                        onChange={e => setUsername(e.target.value.trim())}
                        required
                        style={{ padding: 8, borderRadius: 4, border: "1px solid #ddd" }}
                    />
                    <input
                        type="password"
                        placeholder="Password"
                        value={password}
                        onChange={e => setPassword(e.target.value)}
                        required
                        style={{ padding: 8, borderRadius: 4, border: "1px solid #ddd" }}
                    />
                    <button
                        type="submit"
                        disabled={loading}
                        style={{
                            padding: "8px 0",
                            background: loading ? "#aaa" : "#1976d2",
                            color: "white",
                            border: "none",
                            borderRadius: 4,
                            fontWeight: 600,
                            cursor: loading ? "not-allowed" : "pointer"
                        }}>
                        {loading ? (isRegistering ? "Registering..." : "Logging in...") : (isRegistering ? "Register" : "Login")}
                    </button>
                    <button
                        type="button"
                        onClick={() => {
                            setIsRegistering(!isRegistering);
                            clearError();
                        }}
                        style={{
                            padding: "6px 0",
                            background: "transparent",
                            color: "#1976d2",
                            border: "none",
                            textDecoration: "underline",
                            cursor: "pointer"
                        }}>
                        {isRegistering ? "Already have an account? Login" : "Need an account? Register"}
                    </button>
                </form>
            ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                    <input
                        type="text"
                        placeholder="Username"
                        value={username}
                        onChange={e => setUsername(e.target.value.trim())}
                        required
                        style={{ padding: 8, borderRadius: 4, border: "1px solid #ddd" }}
                    />
                    <button
                        onClick={handlePasskeyLogin}
                        disabled={loading || !username}
                        style={{
                            padding: "8px 0",
                            background: (loading || !username) ? "#aaa" : "#1976d2",
                            color: "white",
                            border: "none",
                            borderRadius: 4,
                            fontWeight: 600,
                            cursor: (loading || !username) ? "not-allowed" : "pointer"
                        }}>
                        {loading ? "Authenticating..." : "Login with Passkey"}
                    </button>
                    <button
                        onClick={handlePasskeyRegister}
                        disabled={loading || !username}
                        style={{
                            padding: "8px 0",
                            background: (loading || !username) ? "#aaa" : "#2e7d32",
                            color: "white",
                            border: "none",
                            borderRadius: 4,
                            fontWeight: 600,
                            cursor: (loading || !username) ? "not-allowed" : "pointer"
                        }}>
                        {loading ? "Registering..." : "Register New Passkey"}
                    </button>
                </div>
            )}

            {error && <div style={{ color: 'red', marginTop: 16 }}>{error}</div>}
        </div>
    );
};

export default AuthPage;
