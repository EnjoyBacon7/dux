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

 const handleTracker = () => {
  navigate("/profile-hub/tracker");
 };

 const handleAdvisor = () => {
  navigate("/profile-hub/advisor");
 };

 const handleCardKeyDown = (handler: () => void) => (e: React.KeyboardEvent) => {
  if (e.key === "Enter" || e.key === " " || e.key === "Spacebar" || e.code === "Space") {
   if (e.key === " " || e.key === "Spacebar" || e.code === "Space") {
    e.preventDefault();
   }
   handler();
  }
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
       onKeyDown={handleCardKeyDown(handleDetailedAnalysis)}
      >
       <div className={styles['profile-hub__feature-icon']}>📊</div>
       <h3 className={styles['profile-hub__feature-title']}>{t("profile_hub.detailed_analysis")}</h3>
       <p className={styles['profile-hub__feature-desc']}>{t("profile_hub.detailed_analysis_desc")}</p>
       <span className={styles['profile-hub__view-btn']}>{t("profile_hub.view_analysis")}</span>
      </div>

      {/* Tracker Card - Clickable */}
      <div
       className={`nb-card ${styles['profile-hub__feature-card']} ${styles['profile-hub__feature-card--clickable']}`}
       onClick={handleTracker}
       role="button"
       tabIndex={0}
       onKeyDown={handleCardKeyDown(handleTracker)}
      >
       <div className={styles['profile-hub__feature-icon']}>📌</div>
       <h3 className={styles['profile-hub__feature-title']}>{t("profile_hub.tracker")}</h3>
       <p className={styles['profile-hub__feature-desc']}>{t("profile_hub.tracker_desc")}</p>
       <span className={styles['profile-hub__view-btn']}>{t("profile_hub.view_tracker")}</span>
      </div>

      {/* Advisor Card - Clickable, centered below the two above */}
      <div
       className={`nb-card ${styles['profile-hub__feature-card']} ${styles['profile-hub__feature-card--clickable']} ${styles['profile-hub__feature-card--centered']}`}
       onClick={handleAdvisor}
       role="button"
       tabIndex={0}
       onKeyDown={handleCardKeyDown(handleAdvisor)}
      >
       <div className={styles['profile-hub__feature-icon']}>💬</div>
       <h3 className={styles['profile-hub__feature-title']}>{t("profile_hub.advisor")}</h3>
       <p className={styles['profile-hub__feature-desc']}>{t("profile_hub.advisor_desc")}</p>
       <span className={styles['profile-hub__view-btn']}>{t("profile_hub.view_advisor")}</span>
      </div>
     </div>
    </div>
   </main>
  </>
 );
};

export default ProfileHub;
