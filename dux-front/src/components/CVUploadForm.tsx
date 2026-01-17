import React, { useRef, useState } from "react";
import { useLanguage } from "../contexts/useLanguage";

interface CVUploadFormProps {
    onSuccess?: () => Promise<void>;
}

const CVUploadForm: React.FC<CVUploadFormProps> = ({ onSuccess }) => {
    const { t } = useLanguage();
    const fileInputRef = useRef<HTMLInputElement | null>(null);
    const [isUploading, setIsUploading] = useState(false);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setSuccessMessage(null);
        setErrorMessage(null);

        const file = fileInputRef.current?.files?.[0];
        if (!file) {
            setErrorMessage(t('upload.no_file_selected'));
            return;
        }

        setIsUploading(true);
        try {
            const formData = new FormData();
            formData.append("file", file);

            const response = await fetch("/api/profile/upload", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || t('upload.failed'));
            }

            const data = await response.json();
            setSuccessMessage(data.message || t('upload.success'));

            // Reset form
            if (fileInputRef.current) {
                fileInputRef.current.value = "";
            }

            // Call parent callback if provided
            if (onSuccess) {
                await onSuccess();
            }
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : t('upload.failed');
            setErrorMessage(message);
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="nb-card home-card">
            <h2 className="home-card-title">{t('upload.title')}</h2>
            <form className="nb-form home-upload-form" onSubmit={handleSubmit}>
                <input
                    type="file"
                    ref={fileInputRef}
                    className="nb-file"
                    disabled={isUploading}
                />
                <button
                    type="submit"
                    className={`nb-btn ${isUploading ? 'nb-btn--ghost' : 'nb-btn--accent'}`}
                    disabled={isUploading}
                >
                    {isUploading ? t('upload.uploading') : t('upload.button')}
                </button>
            </form>
            {successMessage && (
                <div className="nb-alert nb-alert--success nb-mt">{successMessage}</div>
            )}
            {errorMessage && (
                <div className="nb-alert nb-alert--danger nb-mt">{errorMessage}</div>
            )}
        </div>
    );
};

export default CVUploadForm;
