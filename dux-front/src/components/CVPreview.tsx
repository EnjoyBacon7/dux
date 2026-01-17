import React from "react";
import { useLanguage } from "../contexts/useLanguage";

interface CVPreviewProps {
    hasCV: boolean;
    cvFilename?: string | null;
}

const CVPreview: React.FC<CVPreviewProps> = ({ hasCV, cvFilename }) => {
    const { t } = useLanguage();
    const cvUrl = "/api/profile/cv";

    return (
        <div className="nb-card home-card">
            <h2 className="home-card-title">{t('home.cv_title')}</h2>
            {hasCV ? (
                <>
                    <object
                        key={cvFilename || 'cv'}
                        data={cvUrl}
                        type="application/pdf"
                        className="home-cv-frame"
                    >
                        <p className="nb-text-dim">
                            {t('home.cv_preview_unavailable')} {" "}
                            <a
                                className="nb-link"
                                href={cvUrl}
                                target="_blank"
                                rel="noreferrer"
                            >
                                {t('home.cv_open_link')}
                            </a>
                        </p>
                    </object>
                    <div className="home-cv-actions">
                        <a
                            className="nb-link"
                            href={cvUrl}
                            target="_blank"
                            rel="noreferrer"
                        >
                            {t('home.cv_open_link')}
                        </a>
                    </div>
                </>
            ) : (
                <div className="nb-text-dim home-cv-empty">
                    {t('home.cv_missing')}
                </div>
            )}
        </div>
    );
};

export default CVPreview;
