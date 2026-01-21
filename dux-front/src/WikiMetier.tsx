import React, { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Header } from "./components";
import DetailMetier from "./components/DetailMetier";
import "./styles/home.css";
import "./styles/wiki-metier.css";

type MetierItem = {
  romeCode: string;
  romeLibelle: string;
};

const MetierWikiLayout: React.FC = () => {
  const [searchParams] = useSearchParams();
  // 1) Liste des metiers (chargee depuis la base)
  const [items, setItems] = useState<MetierItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCode, setSelectedCode] = useState<string | null>(null);

  // 2) Recherche
  const [q, setQ] = useState("");

  useEffect(() => {
    let isActive = true;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch("/api/metiers");
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        const data = (await res.json()) as MetierItem[];
        if (isActive) {
          setItems(data || []);
        }
      } catch (err) {
        if (isActive) {
          setError(err instanceof Error ? err.message : "Erreur");
          setItems([]);
        }
      } finally {
        if (isActive) {
          setLoading(false);
        }
      }
    }

    load();
    return () => {
      isActive = false;
    };
  }, []);

  const filtered = useMemo(() => {
    const query = q.trim().toLowerCase();
    const base = query
      ? items.filter((m) => {
          return (
            m.romeCode.toLowerCase().includes(query) ||
            m.romeLibelle.toLowerCase().includes(query)
          );
        })
      : items;
    return [...base].sort((a, b) =>
      a.romeLibelle.localeCompare(b.romeLibelle, "fr", { sensitivity: "base" })
    );
  }, [items, q]);

  useEffect(() => {
    const romeFromUrl = searchParams.get("rome");
    if (!romeFromUrl) return;
    setSelectedCode(romeFromUrl);
  }, [searchParams]);

  useEffect(() => {
    if (!selectedCode && items.length > 0) {
      setSelectedCode(items[0].romeCode);
      return;
    }
    if (selectedCode && filtered.length > 0) {
      const stillVisible = filtered.some((m) => m.romeCode === selectedCode);
      const existsInItems = items.some((m) => m.romeCode === selectedCode);
      if (!stillVisible && existsInItems) {
        setSelectedCode(filtered[0].romeCode);
      }
    }
  }, [filtered, items, selectedCode]);

  return (
    <>
      <Header />
      <main className="wiki-metier-shell">
        <div className="wiki-metier-grid">
          {/* Sidebar */}
          <aside className="wiki-metier-sidebar">
            <div className="wiki-metier-sidebar-header">
              <h2 className="wiki-metier-sidebar-title">Metiers</h2>
            </div>

            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Rechercher un metier (ROME ou libelle)"
              className="nb-input wiki-metier-search"
            />

            {loading ? (
              <div className="wiki-metier-empty nb-text-dim">Chargement...</div>
            ) : error ? (
              <div className="wiki-metier-empty nb-text-dim">Erreur: {error}</div>
            ) : filtered.length === 0 ? (
              <div className="wiki-metier-empty nb-text-dim">Aucun resultat.</div>
            ) : (
              <div className="wiki-metier-list">
                {filtered.map((m) => (
                  <button
                    type="button"
                    key={m.romeCode}
                    className={`wiki-metier-link${selectedCode === m.romeCode ? " wiki-metier-link--active" : ""}`}
                    onClick={() => setSelectedCode(m.romeCode)}
                  >
                    <div className="wiki-metier-code">{m.romeLibelle}</div>
                    <div className="wiki-metier-label">{m.romeCode}</div>
                  </button>
                ))}
              </div>
            )}
          </aside>

          {/* Contenu */}
          <section className="wiki-metier-content">
            <div className="wiki-metier-detail-header">
              <h1 className="wiki-metier-title">Wiki des metiers</h1>
              <p className="nb-text-dim">Trouvez un metier par code ROME ou libelle.</p>
            </div>
            {selectedCode ? (
              <DetailMetier romeCode={selectedCode} />
            ) : (
              <div className="wiki-metier-empty nb-text-dim">
                Selectionnez un metier pour afficher la fiche.
              </div>
            )}
          </section>
        </div>
      </main>
    </>
  );
};

export default MetierWikiLayout;
