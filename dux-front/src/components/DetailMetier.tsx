import React, { useEffect, useState } from "react";

export type MetierDetailData = {
  romeCode: string;
  romeLibelle?: string | null;
  definition?: string | null;
  accesEmploi?: string | null;
  competences?: Array<{ libelle: string }>;
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

  useEffect(() => {
    let cancelled = false;

    function mapToDetail(payload: any): MetierDetailData {
      const competences = Array.isArray(payload?.competencesmobilisees)
        ? payload.competencesmobilisees
            .map((item: any) => {
              if (!item) return null;
              if (typeof item === "string") return { libelle: item };
              if (typeof item === "object") {
                const label = item.libelle ?? item.label;
                return label ? { libelle: String(label) } : null;
              }
              return null;
            })
            .filter(Boolean)
        : [];

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
    <div style={{ padding: "1.25rem", maxWidth: "980px" }}>
      <h1 style={{ marginTop: 0 }}>
        {data.romeLibelle ?? "Detail metier"}{" "}
        <span style={{ opacity: 0.6 }}>({data.romeCode})</span>
      </h1>

      <section style={{ marginTop: "1rem", display: "grid", gap: "1rem" }}>
        <div
          style={{
            padding: "0.75rem 1rem",
            border: "1px solid rgba(0,0,0,0.12)",
            borderRadius: "10px",
            maxWidth: "360px",
          }}
        >
          <div style={{ fontSize: "0.85rem", opacity: 0.7 }}>Offres d'emploi</div>
          <div style={{ fontSize: "1.8rem", fontWeight: 700 }}>
            {formatNbOffres(data.nbOffre)}
          </div>
        </div>

        <div
          style={{
            padding: "0.75rem 1rem",
            border: "1px solid rgba(0,0,0,0.12)",
            borderRadius: "10px",
          }}
        >
          <div style={{ fontSize: "0.85rem", opacity: 0.7, marginBottom: "0.5rem" }}>
            Fourchette de salaire (mensuel)
          </div>
          {salaireMin !== null && salaireMax !== null ? (
            <>
              <div style={{ display: "flex", justifyContent: "space-between", fontWeight: 600 }}>
                <span>{formatEur(salaireMin)}</span>
                <span>{formatEur(salaireMax)}</span>
              </div>
              <div style={{ marginTop: "0.5rem" }}>
                <svg width="100%" height="28" viewBox="0 0 100 28" preserveAspectRatio="none">
                  <line x1="5" y1="14" x2="95" y2="14" stroke="rgba(0,0,0,0.2)" strokeWidth="6" />
                  <line x1="5" y1="14" x2="95" y2="14" stroke="#2F6FDE" strokeWidth="6" />
                  <circle cx="5" cy="14" r="6" fill="#1F4EA8" />
                  <circle cx="95" cy="14" r="6" fill="#1F4EA8" />
                  <circle cx={5 + (90 * moyennePct) / 100} cy="14" r="5" fill="#FF8A00" />
                </svg>
              </div>
              {salaireMoyen !== null ? (
                <div style={{ marginTop: "0.35rem", fontSize: "0.85rem", opacity: 0.75 }}>
                  Salaire moyen: {formatEur(salaireMoyen)}
                </div>
              ) : null}
            </>
          ) : (
            <div style={{ opacity: 0.7 }}>Aucune donnee de salaire disponible.</div>
          )}
        </div>
      </section>

      {data.definition ? (
        <section style={{ marginTop: "1rem" }}>
          <h3>Definition</h3>
          <p style={{ lineHeight: 1.55 }}>{data.definition}</p>
        </section>
      ) : null}

      {data.accesEmploi ? (
        <section style={{ marginTop: "1rem" }}>
          <h3>Acces a l'emploi</h3>
          <p style={{ lineHeight: 1.55 }}>{data.accesEmploi}</p>
        </section>
      ) : null}

      {data.competences?.length ? (
        <section style={{ marginTop: "1rem" }}>
          <h3>Competences</h3>
          <ul>
            {data.competences.map((c, idx) => (
              <li key={idx}>{c.libelle}</li>
            ))}
          </ul>
        </section>
      ) : null}

      {data.formations?.length ? (
        <section style={{ marginTop: "1rem" }}>
          <h3>Formations</h3>
          <ul>
            {data.formations.map((f, idx) => (
              <li key={idx}>{f.libelle}</li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
};

export default MetierDetailPanel;
