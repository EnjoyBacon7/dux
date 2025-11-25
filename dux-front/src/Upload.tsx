import React, { useRef, useState } from "react";
import { useLanguage } from "./contexts/useLanguage";
import { Header } from "./components";

const Upload: React.FC = () => {
    const fileInputRef = useRef<HTMLInputElement | null>(null);
    const [uploading, setUploading] = useState(false);
    const [success, setSuccess] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const { t } = useLanguage();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setSuccess(null);
        setError(null);
        const file = fileInputRef.current?.files?.[0];
        if (!file) {
            setError("Please select a file to upload.");
            return;
        }
        setUploading(true);
        try {
            const formData = new FormData();
            formData.append("file", file);
            const res = await fetch("/api/upload", {
                method: "POST",
                body: formData,
            });
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || "Upload failed");
            }
            const data = await res.json();
            setSuccess(data.message || "File uploaded successfully!");
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
            <div className="nb-page nb-card">
                <h1 className="nb-center" style={{ marginTop: 0 }}>{t('upload.title')}</h1>
                <form className="nb-form" onSubmit={handleSubmit}>
                    <input
                        type="file"
                        ref={fileInputRef}
                        className="nb-file"
                        disabled={uploading}
                    />
                    <button type="submit" className={`nb-btn ${uploading ? 'nb-btn--ghost' : 'nb-btn--accent'}`} disabled={uploading}>
                        {uploading ? t('upload.uploading') : t('upload.button')}
                    </button>
                </form>
                {success && <div className="nb-alert nb-alert--success nb-mt">{success}</div>}
                {error && <div className="nb-alert nb-alert--danger nb-mt">{error}</div>}
            </div>
        </>
    );
};

export default Upload;
