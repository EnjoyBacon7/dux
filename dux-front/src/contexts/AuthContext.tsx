import React, { createContext, useState, useCallback, useEffect } from "react";
import type { ReactNode } from "react";
import { useNavigate } from "react-router-dom";

interface User {
    username: string;
    user_id?: number;
    first_name?: string;
    last_name?: string;
    title?: string;
    profile_picture?: string;
    profile_setup_completed?: boolean;
}

interface AuthContextType {
    user: User | null;
    loading: boolean;
    error: string | null;
    signIn: (username: string, password: string) => Promise<void>;
    signUp: (username: string, password: string) => Promise<void>;
    signInWithPasskey: (username: string) => Promise<void>;
    registerPasskey: (username: string) => Promise<void>;
    signOut: () => Promise<void>;
    checkAuth: () => Promise<void>;
    clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export { AuthContext };

// Helper: base64url -> ArrayBuffer
const base64urlToArrayBuffer = (base64url: string): ArrayBuffer => {
    if (typeof base64url !== 'string') throw new Error("Expected base64url string");
    let base64 = base64url.replace(/-/g, '+').replace(/_/g, '/');
    const pad = base64.length % 4;
    if (pad) base64 += '='.repeat(4 - pad);
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
    return bytes.buffer;
};

// Helper: ArrayBuffer -> base64url
const arrayBufferToBase64url = (buffer: ArrayBuffer): string => {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.length; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary)
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=/g, '');
};

// Helper: sanitize username to printable ASCII
const sanitizeUsername = (value: string): string => {
    return value.trim().replace(/[^\x20-\x7E]/g, '');
};

// Types for JSON payloads from backend
type RequestOptionsJSON = {
    challenge: string;
    allowCredentials?: Array<{ id: string; type: PublicKeyCredentialType; transports?: AuthenticatorTransport[] }>;
    userVerification?: 'required' | 'preferred' | 'discouraged';
    rpId?: string;
    timeout?: number;
    extensions?: AuthenticationExtensionsClientInputs;
};

type CreationOptionsJSON = {
    challenge: string;
    rp: { name: string; id?: string };
    user: { id: string; name: string; displayName: string };
    pubKeyCredParams: Array<{ type: PublicKeyCredentialType; alg: number }>;
    timeout?: number;
    excludeCredentials?: Array<{ id: string; type: PublicKeyCredentialType }>;
    authenticatorSelection?: AuthenticatorSelectionCriteria;
    attestation?: AttestationConveyancePreference;
    extensions?: AuthenticationExtensionsClientInputs;
};

const parseMaybeString = <T,>(raw: unknown): T => {
    if (typeof raw === 'string') {
        return JSON.parse(raw) as T;
    }
    return raw as T;
};

const toRequestOptions = (raw: unknown): PublicKeyCredentialRequestOptions => {
    // Some wrappers nest under { publicKey }
    const unwrapped = (raw as Record<string, unknown>)?.publicKey ?? raw;
    const json = parseMaybeString<RequestOptionsJSON>(unwrapped);
    if (!json || !json.challenge) throw new Error('Invalid authentication options: missing challenge');
    const opts: PublicKeyCredentialRequestOptions = {
        challenge: base64urlToArrayBuffer(json.challenge),
        userVerification: json.userVerification,
        rpId: json.rpId,
        timeout: json.timeout,
        allowCredentials: json.allowCredentials?.map((c) => ({
            ...c,
            id: base64urlToArrayBuffer(c.id),
        })),
        extensions: json.extensions,
    };
    return opts;
};

const toCreationOptions = (raw: unknown): PublicKeyCredentialCreationOptions => {
    const unwrapped = (raw as Record<string, unknown>)?.publicKey ?? raw;
    const json = parseMaybeString<CreationOptionsJSON>(unwrapped);
    if (!json || !json.challenge || !json.user?.id) throw new Error('Invalid registration options: missing fields');
    const opts: PublicKeyCredentialCreationOptions = {
        challenge: base64urlToArrayBuffer(json.challenge),
        rp: json.rp,
        user: {
            ...json.user,
            id: base64urlToArrayBuffer(json.user.id),
        },
        pubKeyCredParams: json.pubKeyCredParams,
        timeout: json.timeout,
        excludeCredentials: json.excludeCredentials?.map((c) => ({
            ...c,
            id: base64urlToArrayBuffer(c.id),
        })),
        authenticatorSelection: json.authenticatorSelection as AuthenticatorSelectionCriteria | undefined,
        attestation: json.attestation,
        extensions: json.extensions,
    };
    return opts;
};

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {

    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();

    const checkAuth = useCallback(async () => {
        try {
            const res = await fetch("/auth/me");
            if (res.ok) {
                const data = await res.json();
                setUser(data);
            } else {
                setUser(null);
            }
        } catch {
            setUser(null);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        checkAuth();
    }, [checkAuth]);

    const signIn = useCallback(async (username: string, password: string) => {
        setError(null);
        setLoading(true);
        try {
            username = sanitizeUsername(username);

            const res = await fetch("/auth/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password }),
            });
            if (!res.ok) {
                const err = await res.json().catch(() => ({ detail: "Login failed" }));
                throw new Error(err.detail || err.message || "Login failed");
            }
            await checkAuth();
            navigate("/");
        } catch (err) {
            setError(err instanceof Error ? err.message : "Login failed");
            throw err;
        } finally {
            setLoading(false);
        }
    }, [checkAuth, navigate]);

    const signUp = useCallback(async (username: string, password: string) => {
        setError(null);
        setLoading(true);
        try {
            username = sanitizeUsername(username);

            const res = await fetch("/auth/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password }),
            });
            if (!res.ok) {
                const err = await res.json().catch(() => ({ detail: "Registration failed" }));
                throw new Error(err.detail || err.message || "Registration failed");
            }
            return;
        } catch (err) {
            setError(err instanceof Error ? err.message : "Registration failed");
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    const signInWithPasskey = useCallback(async (username: string) => {
        setError(null);
        setLoading(true);
        try {
            username = sanitizeUsername(username);

            // Get authentication options from server
            const optionsRes = await fetch("/auth/passkey/login-options", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username }),
            });
            if (!optionsRes.ok) {
                const err = await optionsRes.json().catch(() => ({ detail: "Failed to get authentication options" }));
                throw new Error(err.detail || err.message || "Failed to get authentication options");
            }
            const options = toRequestOptions(await optionsRes.json());

            // Use WebAuthn API to get credential
            const credential = await navigator.credentials.get({
                publicKey: options
            }) as PublicKeyCredential | null;

            if (!credential || !credential.response) throw new Error("No credential received");

            const response = credential.response as AuthenticatorAssertionResponse;

            // Convert credential data to base64url (URL-safe base64)
            const credentialData = {
                id: credential.id,
                rawId: arrayBufferToBase64url(credential.rawId),
                response: {
                    authenticatorData: arrayBufferToBase64url(response.authenticatorData),
                    clientDataJSON: arrayBufferToBase64url(response.clientDataJSON),
                    signature: arrayBufferToBase64url(response.signature),
                    userHandle: response.userHandle ? arrayBufferToBase64url(response.userHandle) : null
                },
                type: credential.type
            };

            // Verify credential with server
            const verifyRes = await fetch("/auth/passkey/login-verify", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ credential: credentialData, username }),
            });
            if (!verifyRes.ok) {
                const body = await verifyRes.json().catch(() => null);
                const detail = body?.detail || body?.message || "Authentication failed";
                throw new Error(detail);
            }

            await checkAuth();
            navigate("/");
        } catch (err) {
            setError(err instanceof Error ? err.message : "Passkey authentication failed");
            throw err;
        } finally {
            setLoading(false);
        }
    }, [checkAuth, navigate]);

    const registerPasskey = useCallback(async (username: string) => {
        setError(null);
        setLoading(true);
        try {
            username = sanitizeUsername(username);

            if (!username) {
                throw new Error("Please enter a username");
            }

            // Get registration options from server
            const optionsRes = await fetch("/auth/passkey/register-options", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username }),
            });
            if (!optionsRes.ok) {
                const err = await optionsRes.json().catch(() => ({ detail: "Failed to get registration options" }));
                throw new Error(err.detail || err.message || "Failed to get registration options");
            }
            const options = toCreationOptions(await optionsRes.json());

            // Use WebAuthn API to create credential
            const credential = await navigator.credentials.create({
                publicKey: options
            }) as PublicKeyCredential | null;

            if (!credential || !credential.response) throw new Error("No credential created");

            const response = credential.response as AuthenticatorAttestationResponse;

            // Convert credential data to base64url (URL-safe base64)
            const credentialData = {
                id: credential.id,
                rawId: arrayBufferToBase64url(credential.rawId),
                response: {
                    attestationObject: arrayBufferToBase64url(response.attestationObject),
                    clientDataJSON: arrayBufferToBase64url(response.clientDataJSON)
                },
                type: credential.type
            };

            // Register credential with server
            const registerRes = await fetch("/auth/passkey/register-verify", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ credential: credentialData, username }),
            });
            if (!registerRes.ok) {
                const body = await registerRes.json().catch(() => null);
                const detail = body?.detail || body?.message || "Registration failed";
                throw new Error(detail);
            }

            return;
        } catch (err) {
            setError(err instanceof Error ? err.message : "Passkey registration failed");
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    const signOut = useCallback(async () => {
        setError(null);
        try {
            await fetch("/auth/logout", { method: "POST" });
            setUser(null);
            navigate("/login");
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to log out");
            throw err;
        }
    }, [navigate]);

    const clearError = useCallback(() => {
        setError(null);
    }, []);

    return (
        <AuthContext.Provider
            value={{
                user,
                loading,
                error,
                signIn,
                signUp,
                signInWithPasskey,
                registerPasskey,
                signOut,
                checkAuth,
                clearError
            }}
        >
            {children}
        </AuthContext.Provider>
    );
};
