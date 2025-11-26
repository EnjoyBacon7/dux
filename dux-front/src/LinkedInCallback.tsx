import React, { useEffect } from "react";

/**
 * LinkedIn OAuth callback page
 * This page receives the OAuth callback from LinkedIn and sends the result to the parent window
 */
const LinkedInCallback: React.FC = () => {
    useEffect(() => {
        const handleCallback = async () => {
            try {
                // Get the authorization code and state from URL
                const urlParams = new URLSearchParams(window.location.search);
                const code = urlParams.get('code');
                const state = urlParams.get('state');
                const error = urlParams.get('error');
                const errorDescription = urlParams.get('error_description');

                if (error) {
                    // OAuth error from LinkedIn
                    window.opener?.postMessage({
                        type: 'linkedin-oauth-error',
                        error: errorDescription || error
                    }, window.location.origin);
                    return;
                }

                if (!code || !state) {
                    window.opener?.postMessage({
                        type: 'linkedin-oauth-error',
                        error: 'No authorization code or state received'
                    }, window.location.origin);
                    return;
                }

                // Exchange code for access token and authenticate user
                const response = await fetch('/auth/linkedin/callback', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({ code, state })
                });

                if (!response.ok) {
                    // If callback fails, try the link callback (for authenticated users)
                    const linkResponse = await fetch('/auth/linkedin/link/callback', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include',
                        body: JSON.stringify({ code, state })
                    });

                    if (!linkResponse.ok) {
                        const errorData = await linkResponse.json().catch(() => ({ detail: 'Failed to complete LinkedIn authentication' }));
                        window.opener?.postMessage({
                            type: 'linkedin-oauth-error',
                            error: errorData.detail || 'Failed to complete LinkedIn authentication'
                        }, window.location.origin);
                        return;
                    }
                }

                // Success - notify parent window
                window.opener?.postMessage({
                    type: 'linkedin-oauth-success'
                }, window.location.origin);

            } catch (error) {
                window.opener?.postMessage({
                    type: 'linkedin-oauth-error',
                    error: error instanceof Error ? error.message : 'Unknown error occurred'
                }, window.location.origin);
            }
        };

        handleCallback();
    }, []);

    return (
        <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: '100vh',
            fontFamily: 'system-ui, -apple-system, sans-serif'
        }}>
            <div style={{ textAlign: 'center' }}>
                <h2>Processing LinkedIn authentication...</h2>
                <p>This window will close automatically.</p>
            </div>
        </div>
    );
};

export default LinkedInCallback;
