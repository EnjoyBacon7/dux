import React, { useMemo } from "react";
import { useLanguage } from "../contexts/useLanguage";

interface CVPreviewProps {
    hasCV: boolean;
    cvFilename?: string | null;
}

const CVPreview: React.FC<CVPreviewProps> = ({ hasCV, cvFilename }) => {
    const { t } = useLanguage();
    
    // Add cache-busting parameter based on filename to force refresh when CV changes
    const cvUrl = useMemo(() => {
        const baseUrl = "/api/profile/cv";
        if (cvFilename) {
            // Use filename as cache buster (changes per user/upload)
            return `${baseUrl}?v=${encodeURIComponent(cvFilename)}`;
        }
        return baseUrl;
    }, [cvFilename]);

    return (
        <div className="nb-card home-card cv-preview-card">
            <div className="home-cv-header">
                <h2 className="home-card-title">{t('home.cv_title')}</h2>
                <a
                    className="nb-link"
                    href={cvUrl}
                    target="_blank"
                    rel="noreferrer"
                    title="Open CV in new tab"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="home-cv-icon">
                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                        <polyline points="15 3 21 3 21 9" />
                        <line x1="10" y1="14" x2="21" y2="3" />
                    </svg>
                </a>
            </div>
            {hasCV ? (
                <div className="home-cv-container">
                    <embed
                        key={cvFilename || 'cv'}
                        src={cvUrl}
                        type="application/pdf"
                        className="home-cv-frame"
                    />
                </div>
            ) : (
                <div className="nb-text-dim home-cv-empty">
                    {t('home.cv_missing')}
                </div>
            )}
        </div>
    );
};

export default CVPreview;
