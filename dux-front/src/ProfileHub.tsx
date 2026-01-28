import React from "react";
import { useNavigate } from "react-router-dom";
import { Header } from "./components";
import { useLanguage } from "./contexts/useLanguage";
import { useAuth } from "./contexts/useAuth";
import styles from "./styles/ProfileHub.module.css";

const ProfileHub: React.FC = () => {
    const { t } = useLanguage();
    const { user } = useAuth();
    const navigate = useNavigate();

    if (!user) return null;

    const handleDetailedAnalysis = () => {
        navigate("/profile-hub/detailed-analysis");
    };

    return (
        <>
            <Header />
            <main className="nb-page">
                <div className={styles['profile-hub__content']}>
                    <div className={`nb-card ${styles['profile-hub__header-card']}`}>
                        <h1 className={styles['profile-hub__title']}>{t("profile_hub.title")}</h1>
                        <p className={styles['profile-hub__subtitle']}>{t("profile_hub.subtitle")}</p>
                    </div>

                    <div className={styles['profile-hub__grid']}>
                        {/* Detailed Analysis Card - Now Clickable */}
                        <div 
                            className={`nb-card ${styles['profile-hub__feature-card']} ${styles['profile-hub__feature-card--clickable']}`}
                            onClick={handleDetailedAnalysis}
                            role="button"
                            tabIndex={0}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' || e.key === ' ' || e.key === 'Spacebar' || e.code === 'Space') {
                                    if (e.key === ' ' || e.key === 'Spacebar' || e.code === 'Space') {
                                        e.preventDefault();
                                    }
                                    handleDetailedAnalysis();
                                }
                            }}
                        >
                            <div className={styles['profile-hub__feature-icon']}>📊</div>
                            <h3 className={styles['profile-hub__feature-title']}>{t("profile_hub.detailed_analysis")}</h3>
                            <p className={styles['profile-hub__feature-desc']}>{t("profile_hub.detailed_analysis_desc")}</p>
                            <span className={styles['profile-hub__view-btn']}>{t("profile_hub.view_analysis")}</span>
                        </div>

                        <div className={`nb-card ${styles['profile-hub__feature-card']}`}>
                            <div className={styles['profile-hub__feature-icon']}>🎯</div>
                            <h3 className={styles['profile-hub__feature-title']}>{t("profile_hub.career_path")}</h3>
                            <p className={styles['profile-hub__feature-desc']}>{t("profile_hub.career_path_desc")}</p>
                            <span className={styles['profile-hub__coming-soon']}>{t("profile_hub.coming_soon")}</span>
                        </div>

                        <div className={`nb-card ${styles['profile-hub__feature-card']}`}>
                            <div className={styles['profile-hub__feature-icon']}>💡</div>
                            <h3 className={styles['profile-hub__feature-title']}>{t("profile_hub.skill_gaps")}</h3>
                            <p className={styles['profile-hub__feature-desc']}>{t("profile_hub.skill_gaps_desc")}</p>
                            <span className={styles['profile-hub__coming-soon']}>{t("profile_hub.coming_soon")}</span>
                        </div>

                        <div className={`nb-card ${styles['profile-hub__feature-card']}`}>
                            <div className={styles['profile-hub__feature-icon']}>📝</div>
                            <h3 className={styles['profile-hub__feature-title']}>{t("profile_hub.cv_templates")}</h3>
                            <p className={styles['profile-hub__feature-desc']}>{t("profile_hub.cv_templates_desc")}</p>
                            <span className={styles['profile-hub__coming-soon']}>{t("profile_hub.coming_soon")}</span>
                        </div>
                    </div>
                </div>
            </main>
        </>
    );
};

export default ProfileHub;
