import React, { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./contexts/useAuth";
import { useLanguage } from "./contexts/useLanguage";
import { Header } from "./components";

const ProfileSetup: React.FC = () => {
    const navigate = useNavigate();
    const { checkAuth } = useAuth();
    const { t } = useLanguage();
    const fileInputRef = useRef<HTMLInputElement | null>(null);

    // UI state
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleCvUpload = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        const file = fileInputRef.current?.files?.[0];
        if (!file) {
            setError("Please select a CV file to upload.");
            return;
        }
        setUploading(true);
        try {
            const formData = new FormData();
            formData.append("file", file);
            const res = await fetch("/api/profile/upload", {
                method: "POST",
                body: formData,
            });
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || "Upload failed");
            }

            await checkAuth();
            navigate('/');
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : "Upload failed";
            setError(message);
        } finally {
            setUploading(false);
        }
    };

    return (
        <>
            <Header />
            <div className="nb-page nb-stack">
                <div style={{ maxWidth: '600px', margin: '0 auto', marginBottom: '1.5rem' }}>
                    <h1 className="setup-title">{t('setup.title')}</h1>
                    <p className="nb-text-dim">{t('setup.description')}</p>
                </div>

                {/* CV Upload */}
                <div className="nb-card">
                    <h2 className="setup-step-title">{t('setup.cv_upload')}</h2>
                    <form onSubmit={handleCvUpload} className="setup-form">
                        <input
                            type="file"
                            ref={fileInputRef}
                            className="nb-file"
                            accept=".pdf,.doc,.docx"
                            disabled={uploading}
                        />
                        <div className="setup-form__actions">
                            <button
                                type="submit"
                                className="nb-btn"
                                disabled={uploading}
                            >
                                {uploading ? t('upload.uploading') : t('setup.upload_cv')}
                            </button>
                        </div>
                    </form>
                    {error && <div className="nb-alert nb-alert--danger setup-error">{error}</div>}
                </div>
            </div>
        </>
    );
};

export default ProfileSetup;
