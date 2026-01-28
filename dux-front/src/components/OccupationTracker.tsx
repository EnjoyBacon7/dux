import React, { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Header } from "./index";
import { useLanguage } from "../contexts/useLanguage";
import styles from "../styles/Tracker.module.css";

type FavouriteOccupation = {
  romeCode: string;
  romeLibelle: string;
  addedAt?: string | null;
};

type FavouriteJob = {
  jobId: string;
  intitule: string;
  entreprise_nom?: string | null;
  romeCode?: string | null;
  addedAt?: string | null;
};

const OccupationTracker: React.FC = () => {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [occupations, setOccupations] = useState<FavouriteOccupation[]>([]);
  const [jobs, setJobs] = useState<FavouriteJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [occRes, jobRes] = await Promise.all([
        fetch("/api/metiers/favourites", { credentials: "include" }),
        fetch("/api/jobs/favourites", { credentials: "include" }),
      ]);
      if (!occRes.ok) {
        throw new Error(`HTTP ${occRes.status}`);
      }
      if (!jobRes.ok) {
        throw new Error(`HTTP ${jobRes.status}`);
      }
      const occJson = (await occRes.json()) as { favourites?: FavouriteOccupation[] };
      const jobData = (await jobRes.json()) as FavouriteJob[];
      setOccupations(Array.isArray(occJson?.favourites) ? occJson.favourites : []);
      setJobs(Array.isArray(jobData) ? jobData : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("common.error"));
      setOccupations([]);
      setJobs([]);
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const handleBack = () => {
    navigate("/profile-hub");
  };

  const handleViewFiche = (romeCode: string) => {
    navigate(`/wiki-metier?rome=${encodeURIComponent(romeCode)}`);
  };

  const handleSeeOffers = (romeCode: string) => {
    navigate(`/jobs?codeROME=${encodeURIComponent(romeCode)}`);
  };

  const handleRemoveOccupation = async (romeCode: string) => {
    try {
      const res = await fetch(
        `/api/metiers/favourites/${encodeURIComponent(romeCode)}`,
        { method: "DELETE", credentials: "include" }
      );
      if (res.ok) {
        setOccupations((prev) => prev.filter((r) => r.romeCode !== romeCode));
      }
    } catch (e) {
      console.error("Failed to remove occupation favourite:", e);
    }
  };

  const handleViewJob = (jobId: string) => {
    navigate(`/jobs?open=${encodeURIComponent(jobId)}`);
  };

  const handleRemoveJob = async (jobId: string) => {
    try {
      const res = await fetch(
        `/api/jobs/favourites/${encodeURIComponent(jobId)}`,
        { method: "DELETE", credentials: "include" }
      );
      if (res.ok) {
        setJobs((prev) => prev.filter((j) => j.jobId !== jobId));
      }
    } catch (e) {
      console.error("Failed to remove job favourite:", e);
    }
  };

  if (loading) {
    return (
      <>
        <Header />
        <main className={`nb-page ${styles["tracker-container"]}`}>
          <div className={styles["tracker-loading"]}>
            <div className={styles["tracker-spinner"]} />
            <p>{t("tracker.loading")}</p>
          </div>
        </main>
      </>
    );
  }

  if (error) {
    return (
      <>
        <Header />
        <main className={`nb-page ${styles["tracker-container"]}`}>
          <div className={styles["tracker-error"]}>
            <p>{error}</p>
            <button className="nb-btn nb-btn--accent" onClick={handleBack}>
              {t("tracker.back")}
            </button>
          </div>
        </main>
      </>
    );
  }

  return (
    <>
      <Header />
      <main className={`nb-page ${styles["tracker-container"]}`}>
        <div className={styles["tracker-content"]}>
          <div className={styles["tracker-header"]}>
            <button
              type="button"
              className={styles["tracker-back-btn"]}
              onClick={handleBack}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M19 12H5M12 19l-7-7 7-7" />
              </svg>
              {t("tracker.back")}
            </button>
            <h1 className={styles["tracker-title"]}>{t("tracker.title")}</h1>
          </div>

          {/* Occupations section */}
          <section className={styles["tracker-section"]}>
            <h2 className={styles["tracker-section-title"]}>
              {t("tracker.occupations_section")}
            </h2>
            {occupations.length === 0 ? (
              <div className={styles["tracker-empty"]}>
                <p>{t("tracker.empty_occupations")}</p>
                <button
                  type="button"
                  className="nb-btn nb-btn--accent"
                  onClick={() => navigate("/wiki-metier")}
                >
                  {t("tracker.browse_occupations")}
                </button>
              </div>
            ) : (
              <div className={styles["tracker-list"]}>
                {occupations.map((item) => (
                  <div key={item.romeCode} className={styles["tracker-card"]}>
                    <div className={styles["tracker-card-header"]}>
                      <h3 className={styles["tracker-card-title"]}>
                        {item.romeLibelle || item.romeCode}
                      </h3>
                      <span className={styles["tracker-card-badge"]}>
                        {item.romeCode}
                      </span>
                    </div>
                    <div className={styles["tracker-card-actions"]}>
                      <div className={styles["tracker-card-actions-left"]}>
                        <button
                          type="button"
                          className="nb-btn nb-btn--accent"
                          onClick={() => handleViewFiche(item.romeCode)}
                        >
                          {t("tracker.view_fiche")}
                        </button>
                        <button
                          type="button"
                          className="nb-btn nb-btn--accent"
                          onClick={() => handleSeeOffers(item.romeCode)}
                        >
                          {t("metiers.detail.action_offers")}
                        </button>
                      </div>
                      <button
                        type="button"
                        className={`nb-btn ${styles["tracker-card-actions-remove"]}`}
                        onClick={() => handleRemoveOccupation(item.romeCode)}
                      >
                        {t("tracker.remove")}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Jobs section */}
          <section className={styles["tracker-section"]}>
            <h2 className={styles["tracker-section-title"]}>
              {t("tracker.jobs_section")}
            </h2>
            {jobs.length === 0 ? (
              <div className={styles["tracker-empty"]}>
                <p>{t("tracker.empty_jobs")}</p>
                <button
                  type="button"
                  className="nb-btn nb-btn--accent"
                  onClick={() => navigate("/jobs")}
                >
                  {t("tracker.browse_jobs")}
                </button>
              </div>
            ) : (
              <div className={styles["tracker-list"]}>
                {jobs.map((item) => (
                  <div key={item.jobId} className={styles["tracker-card"]}>
                    <div className={styles["tracker-card-header"]}>
                      <h3 className={styles["tracker-card-title"]}>
                        {item.intitule || item.jobId}
                      </h3>
                      {item.entreprise_nom && (
                        <p className={styles["tracker-card-subtitle"]}>
                          {item.entreprise_nom}
                        </p>
                      )}
                      {item.romeCode && (
                        <span className={styles["tracker-card-badge"]}>
                          {item.romeCode}
                        </span>
                      )}
                    </div>
                    <div className={styles["tracker-card-actions"]}>
                      <div className={styles["tracker-card-actions-left"]}>
                        <button
                          type="button"
                          className="nb-btn nb-btn--accent"
                          onClick={() => handleViewJob(item.jobId)}
                        >
                          {t("tracker.view_job")}
                        </button>
                      </div>
                      <button
                        type="button"
                        className={`nb-btn ${styles["tracker-card-actions-remove"]}`}
                        onClick={() => handleRemoveJob(item.jobId)}
                      >
                        {t("tracker.remove")}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      </main>
    </>
  );
};

export default OccupationTracker;
