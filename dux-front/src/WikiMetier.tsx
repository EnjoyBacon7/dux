import React, { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Header } from "./components";
import DetailMetier from "./components/DetailMetier";
import { useLanguage } from "./contexts/useLanguage";
import "./styles/home.css";
import "./styles/wiki-metier.css";

type MetierItem = {
  romeCode: string;
  romeLibelle: string;
};

const MetierWikiLayout: React.FC = () => {
  const { t } = useLanguage();
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
          setError(err instanceof Error ? err.message : t("common.error"));
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
    if (!romeFromUrl) {
      setSelectedCode(items.length ? items[0].romeCode : null);
      return;
    }
    const existsInItems = items.some((m) => m.romeCode === romeFromUrl);
    setSelectedCode(existsInItems ? romeFromUrl : items.length ? items[0].romeCode : null);
  }, [items, searchParams]);

  useEffect(() => {
    if (selectedCode == null) {
      if (filtered.length > 0) {
        setSelectedCode(filtered[0].romeCode);
        return;
      }
      if (items.length > 0) {
        setSelectedCode(items[0].romeCode);
      }
      return;
    }
    const existsInItems = items.some((m) => m.romeCode === selectedCode);
    if (!existsInItems) {
      setSelectedCode(filtered.length ? filtered[0].romeCode : items.length ? items[0].romeCode : null);
      return;
    }
    if (filtered.length > 0) {
      const stillVisible = filtered.some((m) => m.romeCode === selectedCode);
      if (!stillVisible) {
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
              <h2 className="wiki-metier-sidebar-title">{t("metiers.sidebar_title")}</h2>
            </div>

            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder={t("metiers.search_placeholder")}
              className="nb-input wiki-metier-search"
            />

            {loading ? (
              <div className="wiki-metier-empty nb-text-dim">{t("metiers.loading")}</div>
            ) : error ? (
              <div className="wiki-metier-empty nb-text-dim">
                {t("common.error")}: {error}
              </div>
            ) : filtered.length === 0 ? (
              <div className="wiki-metier-empty nb-text-dim">{t("metiers.no_results")}</div>
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
            {selectedCode ? (
              <DetailMetier romeCode={selectedCode} />
            ) : (
              <div className="wiki-metier-empty nb-text-dim">
                {t("metiers.select_prompt")}
              </div>
            )}
          </section>
        </div>
      </main>
    </>
  );
};

export default MetierWikiLayout;
