import React, { useState, useEffect } from "react";
import { useLanguage } from "../contexts/useLanguage";

interface UserDebugInfo {
    user_info: {
        id: number;
        username: string;
        has_password: boolean;
        created_at: string | null;
        updated_at: string | null;
        is_active: boolean;
        first_name: string | null;
        last_name: string | null;
        title: string | null;
        profile_picture: string | null;
        linkedin_id: string | null;
        failed_login_attempts: number;
        locked_until: string | null;
    };
    passkey_credentials: Array<{
        id: number;
        credential_id: string;
        sign_count: number;
        transports: string | null;
        created_at: string | null;
        last_used_at: string | null;
    }>;
    recent_login_attempts: Array<{
        id: number;
        success: boolean;
        ip_address: string | null;
        user_agent: string | null;
        attempted_at: string | null;
    }>;
    session_info: {
        username: string;
        session_keys: string[];
    };
}

const DebugCard: React.FC = () => {
    const { t } = useLanguage();
    const [debugInfo, setDebugInfo] = useState<UserDebugInfo | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [isExpanded, setIsExpanded] = useState(false);
    const [chatResponse, setChatResponse] = useState<string | null>(null);
    const [isChatLoading, setIsChatLoading] = useState(false);
    const [chatError, setChatError] = useState<string | null>(null);

    useEffect(() => {
        fetchDebugInfo();
    }, []);

    const fetchDebugInfo = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const response = await fetch('/auth/debug/user-info', {
                credentials: 'include'
            });
            if (response.ok) {
                const data = await response.json();
                setDebugInfo(data);
            } else {
                setError(t('debug.failed_fetch'));
            }
        } catch (err) {
            setError(t('debug.error_fetching'));
        } finally {
            setIsLoading(false);
        }
    };

    const formatValue = (value: unknown): string => {
        if (value === null || value === undefined) {
            return 'null';
        }
        if (typeof value === 'boolean') {
            return value ? 'true' : 'false';
        }
        if (typeof value === 'object') {
            return JSON.stringify(value, null, 2);
        }
        return String(value);
    };

    const renderTable = (title: string, data: Record<string, unknown>) => (
        <div style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ margin: '0 0 0.75rem 0', fontSize: '1rem', fontWeight: '600' }}>{title}</h3>
            <div style={{ overflowX: 'auto' }}>
                <table style={{
                    width: '100%',
                    borderCollapse: 'collapse',
                    border: '2px solid var(--nb-border)',
                    fontSize: '0.875rem'
                }}>
                    <thead>
                        <tr style={{ backgroundColor: 'var(--nb-bg-dim)' }}>
                            <th style={{
                                padding: '0.5rem',
                                textAlign: 'left',
                                border: '1px solid var(--nb-border)',
                                fontWeight: '600'
                            }}>
                                Property
                            </th>
                            <th style={{
                                padding: '0.5rem',
                                textAlign: 'left',
                                border: '1px solid var(--nb-border)',
                                fontWeight: '600'
                            }}>
                                Value
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        {Object.entries(data).map(([key, value]) => (
                            <tr key={key}>
                                <td style={{
                                    padding: '0.5rem',
                                    border: '1px solid var(--nb-border)',
                                    fontWeight: '500'
                                }}>
                                    {key}
                                </td>
                                <td style={{
                                    padding: '0.5rem',
                                    border: '1px solid var(--nb-border)',
                                    fontFamily: 'monospace',
                                    wordBreak: 'break-all'
                                }}>
                                    {formatValue(value)}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );

    const renderArrayTable = (title: string, items: Array<Record<string, unknown>>) => {
        if (items.length === 0) {
            return (
                <div style={{ marginBottom: '1.5rem' }}>
                    <h3 style={{ margin: '0 0 0.75rem 0', fontSize: '1rem', fontWeight: '600' }}>{title}</h3>
                    <p style={{ color: 'var(--nb-text-dim)', fontStyle: 'italic' }}>No items</p>
                </div>
            );
        }

        const columns = Object.keys(items[0]);

        return (
            <div style={{ marginBottom: '1.5rem' }}>
                <h3 style={{ margin: '0 0 0.75rem 0', fontSize: '1rem', fontWeight: '600' }}>{title}</h3>
                <div style={{ overflowX: 'auto' }}>
                    <table style={{
                        width: '100%',
                        borderCollapse: 'collapse',
                        border: '2px solid var(--nb-border)',
                        fontSize: '0.875rem'
                    }}>
                        <thead>
                            <tr style={{ backgroundColor: 'var(--nb-bg-dim)' }}>
                                {columns.map(col => (
                                    <th key={col} style={{
                                        padding: '0.5rem',
                                        textAlign: 'left',
                                        border: '1px solid var(--nb-border)',
                                        fontWeight: '600'
                                    }}>
                                        {col}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {items.map((item, idx) => (
                                <tr key={idx}>
                                    {columns.map(col => (
                                        <td key={col} style={{
                                            padding: '0.5rem',
                                            border: '1px solid var(--nb-border)',
                                            fontFamily: col !== 'user_agent' ? 'monospace' : 'inherit',
                                            wordBreak: 'break-all',
                                            fontSize: col === 'user_agent' ? '0.75rem' : '0.875rem'
                                        }}>
                                            {formatValue(item[col])}
                                        </td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        );
    };

    return (
        <div className="nb-card home-card debug-card">
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '1rem'
            }}>
                <div>
                    <h2 style={{ margin: 0, fontSize: '1.25rem' }}>🐛 {t('debug.title')}</h2>
                    <p className="nb-text-dim" style={{ margin: '0.25rem 0 0 0', fontSize: '0.875rem' }}>
                        {t('debug.description')}
                    </p>
                </div>
                <button
                    className="nb-btn nb-btn-sm"
                    onClick={fetchDebugInfo}
                    disabled={isLoading}
                >
                    {isLoading ? t('debug.loading') : t('debug.refresh')}
                </button>
            </div>

            {error && (
                <div style={{
                    padding: '0.75rem',
                    backgroundColor: 'var(--nb-error-bg)',
                    border: '2px solid var(--nb-error)',
                    marginBottom: '1rem'
                }}>
                    <strong>{t('common.error')}:</strong> {error}
                </div>
            )}

            {debugInfo && (
                <div>
                    <button
                        className="nb-btn nb-btn-outline"
                        onClick={() => setIsExpanded(!isExpanded)}
                        style={{ marginBottom: '1rem', width: '100%' }}
                    >
                        {isExpanded ? `▼ ${t('debug.hide_details')}` : `▶ ${t('debug.show_details')}`}
                    </button>

                    {isExpanded && (
                        <>
                            {renderTable(t('debug.user_info'), debugInfo.user_info)}
                            {renderTable(t('debug.session_info'), debugInfo.session_info)}
                            {renderArrayTable(t('debug.passkey_credentials'), debugInfo.passkey_credentials)}
                            {renderArrayTable(t('debug.login_attempts'), debugInfo.recent_login_attempts)}
                        </>
                    )}
                </div>
            )}

            {isLoading && !debugInfo && (
                <div style={{ textAlign: 'center', padding: '2rem' }}>
                    <p>{t('debug.loading_info')}</p>
                </div>
            )}

            <div style={{ marginTop: '2rem', paddingTop: '1.5rem', borderTop: '2px solid var(--nb-border)' }}>
                <h3 style={{ margin: '0 0 1rem 0', fontSize: '1rem', fontWeight: '600' }}>🤖 {t('debug.test_matching')}</h3>

                <div style={{ marginBottom: '1rem' }}>
                    <button
                        className="nb-btn"
                        onClick={async () => {
                            setIsChatLoading(true);
                            setChatError(null);
                            setChatResponse(null);
                            try {
                                const response = await fetch('/api/chat/optimal_offers', {
                                    credentials: 'include'
                                });
                                if (response.ok) {
                                    const data = await response.json();
                                    setChatResponse(JSON.stringify(data, null, 2));
                                } else {
                                    const error = await response.json();
                                    setChatError(error.detail || t('errors.failed_model_response'));
                                }
                            } catch (err) {
                                setChatError(t('errors.error_sending_request'));
                            } finally {
                                setIsChatLoading(false);
                            }
                        }}
                        disabled={isChatLoading}
                        style={{ width: '100%' }}
                    >
                        {isChatLoading ? t('debug.sending') : 'Get Optimal Offers'}
                    </button>
                </div>

                {chatError && (
                    <div style={{
                        padding: '0.75rem',
                        backgroundColor: 'var(--nb-error-bg)',
                        border: '2px solid var(--nb-error)',
                        marginBottom: '1rem',
                        fontSize: '0.875rem'
                    }}>
                        <strong>{t('common.error')}:</strong> {chatError}
                    </div>
                )}

                {chatResponse && (
                    <div style={{
                        padding: '0.75rem',
                        backgroundColor: 'var(--nb-bg-dim)',
                        border: '2px solid var(--nb-border)',
                        borderRadius: '0.25rem'
                    }}>
                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600', fontSize: '0.875rem' }}>
                            {t('debug.response')}
                        </label>
                        <textarea
                            value={chatResponse}
                            readOnly
                            style={{
                                width: '100%',
                                minHeight: '200px',
                                padding: '0.75rem',
                                border: '2px solid var(--nb-border)',
                                backgroundColor: 'var(--nb-bg)',
                                color: 'var(--nb-text)',
                                fontSize: '0.875rem',
                                fontFamily: 'monospace',
                                boxSizing: 'border-box'
                            }}
                        />
                    </div>
                )}
            </div>
        </div>
    );
};

export default DebugCard;
