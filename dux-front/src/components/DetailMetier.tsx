import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useLanguage } from "../contexts/useLanguage";
import styles from "../styles/wiki-metier.module.css";

// Helper to create CSS custom properties with proper typing
const delayStyle = (delay: string) => ({ "--delay": delay } as React.CSSProperties);

export type MetierDetailData = {
  romeCode: string;
  romeLibelle?: string | null;
  definition?: string | null;
  accesEmploi?: string | null;
  competences?: Array<{ libelle: string; code?: string | null }>;
  formations?: Array<{ libelle: string }>;
  nbOffre?: number | null;
  listeSalaireOffre?: number[];
};

type Props = {
  romeCode: string;
  apiBaseUrl?: string;
};

const MetierDetailPanel: React.FC<Props> = ({ romeCode, apiBaseUrl = "" }) => {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [data, setData] = useState<MetierDetailData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [err, setErr] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [cvComparisonText, setCvComparisonText] = useState<string>("Loading CV...");

  useEffect(() => {
    let cancelled = false;

    function mapToDetail(payload: any): MetierDetailData {
      const normalizeCompetences = (
        input: any
      ): Array<{ libelle: string; code?: string | null }> => {
        if (!input) return [];
        if (Array.isArray(input)) {
          return input
            .map((item: any) => {
              if (!item) return null;
              if (typeof item === "string") return { libelle: item };
              if (typeof item === "object") {
                const label =
                  item.libelle ??
                  item.label ??
                  item.name ??
                  item.titre ??
                  item?.competence?.libelle ??
                  item?.competenceDetaillee?.libelle ??
                  item?.competencedetaillee?.libelle ??
                  item?.macroSavoirEtreProfessionnel?.libelle ??
                  item?.macrosavoiretreprofessionnel?.libelle ??
                  item?.macroSavoirFaire?.libelle ??
                  item?.macrosavoirfaire?.libelle;
                const code =
                  item.code ??
                  item.codeogr ??
                  item?.competence?.code ??
                  item?.competenceDetaillee?.code ??
                  item?.competencedetaillee?.code ??
                  item?.macroSavoirEtreProfessionnel?.code ??
                  item?.macrosavoiretreprofessionnel?.code ??
                  item?.macroSavoirFaire?.code ??
                  item?.macrosavoirfaire?.code;
                return label ? { libelle: String(label), code: code ? String(code) : null } : null;
              }
              return null;
            })
            .filter(Boolean) as Array<{ libelle: string; code?: string | null }>;
        }
        if (typeof input === "string") return [{ libelle: input }];
        if (typeof input === "object") {
          if (Array.isArray(input.competences)) return normalizeCompetences(input.competences);
          if (Array.isArray(input.competence)) return normalizeCompetences(input.competence);
          if (Array.isArray(input.items)) return normalizeCompetences(input.items);
          const label =
            input.libelle ??
            input.label ??
            input.name ??
            input.titre ??
            input?.competence?.libelle ??
            input?.competenceDetaillee?.libelle ??
            input?.competencedetaillee?.libelle ??
            input?.macroSavoirEtreProfessionnel?.libelle ??
            input?.macrosavoiretreprofessionnel?.libelle ??
            input?.macroSavoirFaire?.libelle ??
            input?.macrosavoirfaire?.libelle;
          const code =
            input.code ??
            input.codeogr ??
            input?.competence?.code ??
            input?.competenceDetaillee?.code ??
            input?.competencedetaillee?.code ??
            input?.macroSavoirEtreProfessionnel?.code ??
            input?.macrosavoiretreprofessionnel?.code ??
            input?.macroSavoirFaire?.code ??
            input?.macrosavoirfaire?.code;
          return label
            ? [{ libelle: String(label), code: code ? String(code) : null }]
            : [];
        }
        return [];
      };

      const normalizeText = (input: any): string | null => {
        if (!input) return null;
        if (typeof input === "string") return input;
        if (Array.isArray(input)) {
          const parts = input
            .map((item: any) => normalizeText(item))
            .filter((item: any) => typeof item === "string" && item.trim());
          return parts.length ? parts.join("\n") : null;
        }
        if (typeof input === "object") {
          const candidate =
            input.libelle ??
            input.label ??
            input.texte ??
            input.description ??
            input.content ??
            input.value;
          return typeof candidate === "string" ? candidate : null;
        }
        return null;
      };

      const rawCompetences =
        payload?.competencesmobiliseesprincipales ??
        payload?.competencesMobiliseesPrincipales ??
        payload?.competences_mobilisees_principales ??
        payload?.competencesmobilisees ??
        payload?.competencesMobilisees ??
        payload?.competences_mobilisees ??
        payload?.competences ??
        payload?.competence;

      const competences = normalizeCompetences(rawCompetences);

      return {
        romeCode: payload?.code ?? romeCode,
        romeLibelle: payload?.libelle ?? null,
        definition: normalizeText(payload?.definition),
        accesEmploi: normalizeText(payload?.accesemploi ?? payload?.accesEmploi),
        competences,
        formations: [],
        nbOffre: typeof payload?.nb_offre === "number" ? payload.nb_offre : null,
        listeSalaireOffre: Array.isArray(payload?.liste_salaire_offre)
          ? payload.liste_salaire_offre.filter((val: any) => typeof val === "number")
          : [],
      };
    }

    async function load() {
      setLoading(true);
      setErr(null);
      setData(null);

      try {
        const url = `${apiBaseUrl}/api/jobs/load_fiche_metier?codeROME=${encodeURIComponent(romeCode)}`;
        const res = await fetch(url, { method: "POST" });

        if (!res.ok) {
          throw new Error(`HTTP ${res.status} - ${res.statusText}`);
        }

        const json = await res.json();
        if (json?.error) {
          throw new Error(String(json.error));
        }

        if (!cancelled) setData(mapToDetail(json));
      } catch (e: any) {
        if (!cancelled) setErr(e?.message ?? t("metiers.detail.error_unknown"));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    if (romeCode) load();

    return () => {
      cancelled = true;
    };
  }, [romeCode, apiBaseUrl,t]);

  useEffect(() => {
    setIsExpanded(false);
  }, [romeCode]);

  useEffect(() => {
    let cancelled = false;

    const buildCvComparisonText = (cvTextValue: string | null) => {
      const cleaned = (cvTextValue ?? "").replace(/\s+/g, " ").trim();
      if (!cleaned) {
        return "No CV text available yet.";
      }
      const preview = cleaned.length > 240 ? `${cleaned.slice(0, 240)}...` : cleaned;
      return `CV preview: ${preview}`;
    };

    async function loadCvText() {
      try {
        const url = `${apiBaseUrl}/api/metiers/cv_text`;
        const res = await fetch(url);
        if (!res.ok) {
          throw new Error(`HTTP ${res.status} - ${res.statusText}`);
        }
        const json = await res.json();
        if (!cancelled) {
          setCvComparisonText(buildCvComparisonText(json?.cvText ?? null));
        }
      } catch (e: any) {
        if (!cancelled) {
          setCvComparisonText("Unable to load CV text.");
        }
      }
    }

    loadCvText();

    return () => {
      cancelled = true;
    };
  }, [apiBaseUrl]);

  const resume = useMemo(() => {
    if (!data?.definition) return t("metiers.detail.summary_fallback");
    const normalized = data.definition.replace(/\s+/g, " ").trim();
    const match = normalized.match(/.*?[.!?](\s|$)/);
    return (match ? match[0] : normalized).trim();
  }, [data?.definition, t]);

  const renderDefinition = (text: string) => {
    const parts = text.split(/\\n|\r\n|\n/);
    return parts.map((chunk, index) => (
      <React.Fragment key={index}>
        {chunk}
        {index < parts.length - 1 ? <br /> : null}
      </React.Fragment>
    ));
  };

  if (loading) {
    return <div style={{ padding: "1rem" }}>{t("metiers.detail.loading")}</div>;
  }

  if (err) {
    return (
      <div style={{ padding: "1rem" }}>
        <div style={{ fontWeight: 700, marginBottom: "0.5rem" }}>{t("common.error")}</div>
        <div style={{ opacity: 0.85 }}>{err}</div>
      </div>
    );
  }

  if (!data) {
    return <div style={{ padding: "1rem" }}>{t("metiers.detail.no_data")}</div>;
  }

  const salaires = (data.listeSalaireOffre ?? []).filter(
    (v) => Number.isFinite(v) && v > 0
  );
  const salairesFiltres = (() => {
    if (salaires.length < 10) return salaires;
    const sorted = [...salaires].sort((a, b) => a - b);
    const cut = Math.floor(sorted.length * 0.1);
    return sorted.slice(cut, sorted.length - cut);
  })();
  const salaireMin = salairesFiltres.length ? Math.min(...salairesFiltres) : null;
  const salaireMax = salairesFiltres.length ? Math.max(...salairesFiltres) : null;
  const salaireMoyen = salairesFiltres.length
    ? salairesFiltres.reduce((sum, v) => sum + v, 0) / salairesFiltres.length
    : null;
  const range = salaireMin !== null && salaireMax !== null ? salaireMax - salaireMin : 0;
  const moyennePct =
    salaireMin !== null && salaireMax !== null && range > 0 && salaireMoyen !== null
      ? Math.min(100, Math.max(0, ((salaireMoyen - salaireMin) / range) * 100))
      : 50;

  const formatEur = (value: number | null) =>
    value === null ? "--" : `${Math.round(value).toLocaleString("fr-FR")} EUR`;
  const formatNbOffres = (value: number | null | undefined) => {
    if (!value || value <= 0) return "0";
    if (value >= 3000) return "3000+";
    return value.toLocaleString("fr-FR");
  };

  return (
    <div className={styles["wiki-metier-detail"]} key={romeCode}>
      <section className={`${styles["wm-card"]} ${styles["wm-hero"]}`} style={delayStyle("0.02s")}>
        <div className={styles["wm-hero-title-row"]}>
          <h2 className={styles["wm-hero-title"]}>{data.romeLibelle ?? t("metiers.detail.title_fallback")}</h2>
          <span className={styles["wm-rome-badge"]}>{data.romeCode}</span>
        </div>
        <p className={styles["wm-hero-summary"]}>{renderDefinition(resume)}</p>
      </section>

      <section className={`${styles["wm-card"]} ${styles["wm-hero"]}`} style={delayStyle("0.02s")}>
        <div className={styles["wm-card-header"]}>
          <h3>{t("metiers.detail.title_cv_comparison")}</h3>
        </div>
        <p className={styles["wm-hero-summary"]}>{cvComparisonText}</p>
      </section>

      <div className={styles["wm-detail-grid"]}>
        <div className={styles["wm-main-column"]}>

          <section className={styles["wm-card"]} style={delayStyle("0.14s")}>
            <div className={styles["wm-card-header"]}>
              <h3>{t("metiers.detail.role_title")}</h3>
            </div>
            {data.definition ? (
            <p
              className={`wm-body wm-body--definition wm-body--clamp ${
                isExpanded ? "wm-body--expanded" : ""
              }`}
            >
              {renderDefinition(data.definition)}
            </p>
          ) : (
              <p className={`${styles["wm-body"]} ${styles["wm-muted"]}`}>{t("metiers.detail.description_missing")}</p>
            )}
            {data.definition ? (
              <button
                type="button"
                className={styles["wm-link-btn"]}
                onClick={() => setIsExpanded((prev) => !prev)}
                aria-expanded={isExpanded}
              >
                {isExpanded ? t("metiers.detail.see_less") : t("metiers.detail.see_more")}
              </button>
            ) : null}

        {data.accesEmploi ? (
          <div className={styles["wm-subsection"]}>
            <h4>{t("metiers.detail.training_access_title")}</h4>
            <p className={`${styles["wm-body"]} ${styles["wm-body--tight"]}`}>{data.accesEmploi}</p>
          </div>
        ) : null}
          </section>

          <section className={styles["wm-card"]} style={delayStyle("0.08s")}>
            <div className={styles["wm-card-header"]}>
              <h3>{t("metiers.detail.key_metrics")}</h3>
            </div>
            <div className={styles["wm-stats-grid"]}>
              <div className={styles["wm-stat"]}>
                <div className={styles["wm-stat-label"]}>{t("metiers.detail.stats.offers")}</div>
                <div className={styles["wm-stat-value"]}>{formatNbOffres(data.nbOffre)}</div>
                <div className={styles["wm-stat-sub"]}>{t("metiers.detail.stats.offers_active")}</div>
              </div>
              <div className={styles["wm-stat"]}>
                <div className={styles["wm-stat-label"]}>{t("metiers.detail.stats.avg_salary")}</div>
                <div className={styles["wm-stat-value"]}>
                  {salaireMoyen !== null ? formatEur(salaireMoyen) : "--"}
                </div>
                <div className={styles["wm-stat-sub"]}>{t("metiers.detail.stats.monthly")}</div>
              </div>
              <div className={styles["wm-stat"]}>
                <div className={styles["wm-stat-label"]}>{t("metiers.detail.stats.range")}</div>
                <div className={styles["wm-stat-value"]}>
                  {salaireMin !== null && salaireMax !== null
                    ? `${formatEur(salaireMin)} - ${formatEur(salaireMax)}`
                    : "--"}
                </div>
                <div className={styles["wm-stat-sub"]}>{t("metiers.detail.stats.min_max")}</div>
              </div>
            </div>

            <div className={styles["wm-salary-range"]}>
              <div className={styles["wm-salary-header"]}>{t("metiers.detail.salary_range_title")}</div>
              {salaireMin !== null && salaireMax !== null ? (
                <>
                  <div className={styles["wm-salary-track"]}>
                    <div className={styles["wm-salary-gradient"]} />
                    <div
                      className={styles["wm-salary-thumb"]}
                      style={{ left: `${moyennePct}%` }}
                      aria-hidden="true"
                    />
                  </div>
                  <div className={styles["wm-salary-labels"]}>
                    <span>{formatEur(salaireMin)}</span>
                    <span>{formatEur(salaireMax)}</span>
                  </div>
                  {salaireMoyen !== null ? (
                    <div className={styles["wm-salary-mean"]}>
                      {t("metiers.detail.salary_mean")}: {formatEur(salaireMoyen)}
                    </div>
                  ) : null}
                </>
              ) : (
                <div className={styles["wm-muted"]}>{t("metiers.detail.salary_no_data")}</div>
              )}
            </div>
          </section>

          <section className={styles["wm-card"]} style={delayStyle("0.26s")}>
            <div className={styles["wm-card-header"]}>
              <h3>{t("metiers.detail.actions_title")}</h3>
            </div>
            <div className={styles["wm-actions"]}>
              <button
                type="button"
                className={`nb-btn ${styles["wm-action-btn"]}`}
                onClick={() => navigate(`/jobs?codeROME=${encodeURIComponent(data.romeCode)}`)}
              >
                {t("metiers.detail.action_offers")}
              </button>
              <button type="button" className={`nb-btn ${styles["wm-action-btn"]}`}>
                {t("metiers.detail.action_favorite")}
              </button>
            </div>
          </section>
        </div>

        <aside className={styles["wm-aside-column"]}>
          <section className={styles["wm-card"]} style={delayStyle("0.2s")}>
            <div className={styles["wm-card-header"]}>
              <h3>{t("metiers.detail.skills_title")}</h3>
            </div>
            {data.competences?.length ? (
              <div className={styles["wm-skill-wall"]}>
                {data.competences.map((c, idx) => (
                  <span key={idx} className={styles["wm-skill-chip"]} title={c.code ?? c.libelle}>
                    {c.libelle}
                  </span>
                ))}
              </div>
            ) : (
              <div className={styles["wm-muted"]}>{t("metiers.detail.skills_empty")}</div>
            )}
          </section>
        </aside>
      </div>
    </div>
  );
};

export default MetierDetailPanel;
