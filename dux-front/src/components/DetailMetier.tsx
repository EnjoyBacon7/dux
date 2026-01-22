import React, { useEffect, useMemo, useState } from "react";

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
  const [data, setData] = useState<MetierDetailData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [err, setErr] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

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
        definition: payload?.definition ?? null,
        accesEmploi: payload?.accesemploi ?? null,
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
        if (!cancelled) setErr(e?.message ?? "Erreur inconnue");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    if (romeCode) load();

    return () => {
      cancelled = true;
    };
  }, [romeCode, apiBaseUrl]);

  useEffect(() => {
    setIsExpanded(false);
  }, [romeCode]);

  const resume = useMemo(() => {
    if (!data?.definition) return "Description non disponible pour ce metier.";
    const normalized = data.definition.replace(/\s+/g, " ").trim();
    const match = normalized.match(/.*?[.!?](\s|$)/);
    return (match ? match[0] : normalized).trim();
  }, [data?.definition]);

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
    return <div style={{ padding: "1rem" }}>Chargement du metier...</div>;
  }

  if (err) {
    return (
      <div style={{ padding: "1rem" }}>
        <div style={{ fontWeight: 700, marginBottom: "0.5rem" }}>Erreur</div>
        <div style={{ opacity: 0.85 }}>{err}</div>
      </div>
    );
  }

  if (!data) {
    return <div style={{ padding: "1rem" }}>Aucune donnee disponible.</div>;
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
    <div className="wiki-metier-detail" key={romeCode}>
      <section className="wm-card wm-hero" style={{ ["--delay" as any]: "0.02s" }}>
        <div className="wm-hero-title-row">
          <h2 className="wm-hero-title">{data.romeLibelle ?? "Detail metier"}</h2>
          <span className="wm-rome-badge">{data.romeCode}</span>
        </div>
        <p className="wm-hero-summary">{renderDefinition(resume)}</p>
      </section>

      <div className="wm-detail-grid">
        <div className="wm-main-column">

          <section className="wm-card" style={{ ["--delay" as any]: "0.14s" }}>
            <div className="wm-card-header">
              <h3>Role et missions principales</h3>
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
              <p className="wm-body wm-muted">Aucune description disponible.</p>
            )}
            {data.definition ? (
              <button
                type="button"
                className="wm-link-btn"
                onClick={() => setIsExpanded((prev) => !prev)}
                aria-expanded={isExpanded}
              >
                {isExpanded ? "Voir moins" : "Voir plus"}
              </button>
            ) : null}

            {data.accesEmploi ? (
              <div className="wm-subsection">
                <h4>Acces a l'emploi</h4>
                <p className="wm-body wm-body--tight">{data.accesEmploi}</p>
              </div>
            ) : null}

            {data.formations?.length ? (
              <div className="wm-subsection">
                <h4>Formations</h4>
                <ul className="wm-list">
                  {data.formations.map((f, idx) => (
                    <li key={idx}>{f.libelle}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </section>

          <section className="wm-card" style={{ ["--delay" as any]: "0.08s" }}>
            <div className="wm-card-header">
              <h3>Indicateurs cles</h3>
            </div>
            <div className="wm-stats-grid">
              <div className="wm-stat">
                <div className="wm-stat-label">Offres</div>
                <div className="wm-stat-value">{formatNbOffres(data.nbOffre)}</div>
                <div className="wm-stat-sub">offres actives</div>
              </div>
              <div className="wm-stat">
                <div className="wm-stat-label">Salaire moyen</div>
                <div className="wm-stat-value">
                  {salaireMoyen !== null ? formatEur(salaireMoyen) : "--"}
                </div>
                <div className="wm-stat-sub">mensuel</div>
              </div>
              <div className="wm-stat">
                <div className="wm-stat-label">Fourchette</div>
                <div className="wm-stat-value">
                  {salaireMin !== null && salaireMax !== null
                    ? `${formatEur(salaireMin)} - ${formatEur(salaireMax)}`
                    : "--"}
                </div>
                <div className="wm-stat-sub">min / max</div>
              </div>
            </div>

            <div className="wm-salary-range">
              <div className="wm-salary-header">Fourchette de salaire (mensuel)</div>
              {salaireMin !== null && salaireMax !== null ? (
                <>
                  <div className="wm-salary-track">
                    <div className="wm-salary-gradient" />
                    <div
                      className="wm-salary-thumb"
                      style={{ left: `${moyennePct}%` }}
                      aria-hidden="true"
                    />
                  </div>
                  <div className="wm-salary-labels">
                    <span>{formatEur(salaireMin)}</span>
                    <span>{formatEur(salaireMax)}</span>
                  </div>
                  {salaireMoyen !== null ? (
                    <div className="wm-salary-mean">
                      Salaire moyen: {formatEur(salaireMoyen)}
                    </div>
                  ) : null}
                </>
              ) : (
                <div className="wm-muted">Aucune donnee de salaire disponible.</div>
              )}
            </div>
          </section>

          <section className="wm-card wm-actions-card" style={{ ["--delay" as any]: "0.26s" }}>
            <div className="wm-card-header">
              <h3>Actions</h3>
            </div>
            <div className="wm-actions">
              <button type="button" className="nb-btn wm-action-btn">
                Voir les offres liees
              </button>
              <button type="button" className="nb-btn wm-action-btn">
                Comparer avec mon CV
              </button>
              <button type="button" className="nb-btn wm-action-btn">
                Ajouter aux favoris
              </button>
            </div>
          </section>
        </div>

        <aside className="wm-aside-column">
          <section className="wm-card" style={{ ["--delay" as any]: "0.2s" }}>
            <div className="wm-card-header">
              <h3>Competences</h3>
            </div>
            {data.competences?.length ? (
              <div className="wm-skill-wall">
                {data.competences.map((c, idx) => (
                  <span key={idx} className="wm-skill-chip" title={c.code ?? c.libelle}>
                    {c.libelle}
                  </span>
                ))}
              </div>
            ) : (
              <div className="wm-muted">Aucune competence renseignee.</div>
            )}
          </section>
        </aside>
      </div>
    </div>
  );
};

export default MetierDetailPanel;
