import React, { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Header } from "./components";
import DetailMetier from "./components/DetailMetier";
import { useLanguage } from "./contexts/useLanguage";
import "./styles/home.css";
import styles from "./styles/wiki-metier.module.css";

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
    const hasTriggeredPopulate = useRef(false);

    // 2) Recherche
    const [q, setQ] = useState("");

    useEffect(() => {
        let isActive = true;

        async function populateIfEmpty() {
            if (hasTriggeredPopulate.current) return false;
            try {
                const res = await fetch("/api/jobs/load_code_metier", { method: "POST" });
                if (!res.ok) {
                    hasTriggeredPopulate.current = false;
                    throw new Error(`HTTP ${res.status}`);
                }
                hasTriggeredPopulate.current = true;
                return true;
            } catch (err) {
                hasTriggeredPopulate.current = false;
                throw err;
            }
        }

        async function load() {
            setLoading(true);
            setError(null);
            try {
                const res = await fetch("/api/metiers");
                if (!res.ok) {
                    throw new Error(`HTTP ${res.status}`);
                }
                let data = (await res.json()) as MetierItem[];
                if (isActive && (!data || data.length === 0)) {
                    const didPopulate = await populateIfEmpty();
                    if (didPopulate) {
                        const retry = await fetch("/api/metiers");
                        if (!retry.ok) {
                            throw new Error(`HTTP ${retry.status}`);
                        }
                        data = (await retry.json()) as MetierItem[];
                    }
                }
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
    }, [t]);

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

    const romeParam = useMemo(() => {
        const value = searchParams.get("rome");
        return value ? value.trim().toUpperCase() : null;
    }, [searchParams]);

    useEffect(() => {
        if (romeParam) {
            setSelectedCode(romeParam);
            return;
        }
        setSelectedCode(items.length ? items[0].romeCode : null);
    }, [items, romeParam]);

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
        if (romeParam && selectedCode === romeParam) {
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
             <main className={styles['wiki-metier-shell']}>
                 <div className={styles['wiki-metier-grid']}>
                     {/* Sidebar */}
                     <aside className={styles['wiki-metier-sidebar']}>
                         <div className={styles['wiki-metier-sidebar-header']}>
                             <h2 className={styles['wiki-metier-sidebar-title']}>{t("metiers.sidebar_title")}</h2>
                         </div>

                         <input
                             value={q}
                             onChange={(e) => setQ(e.target.value)}
                             placeholder={t("metiers.search_placeholder")}
                             className="nb-input wiki-metier-search"
                         />

                         {loading ? (
                             <div className={`${styles['wiki-metier-empty']} nb-text-dim`}>{t("metiers.loading")}</div>
                         ) : error ? (
                             <div className={`${styles['wiki-metier-empty']} nb-text-dim`}>
                                 {t("common.error")}: {error}
                             </div>
                         ) : filtered.length === 0 ? (
                             <div className={`${styles['wiki-metier-empty']} nb-text-dim`}>{t("metiers.no_results")}</div>
                         ) : (
                             <div className={styles['wiki-metier-list']}>
                                 {filtered.map((m) => (
                                     <button
                                         type="button"
                                         key={m.romeCode}
                                         className={`${styles['wiki-metier-link']}${selectedCode === m.romeCode ? ` ${styles['wiki-metier-link--active']}` : ""}`}
                                         onClick={() => setSelectedCode(m.romeCode)}
                                     >
                                         <div className={styles['wiki-metier-code']}>{m.romeLibelle}</div>
                                         <div className={styles['wiki-metier-label']}>{m.romeCode}</div>
                                     </button>
                                 ))}
                             </div>
                         )}
                     </aside>

                     {/* Contenu */}
                     <section className={styles['wiki-metier-content']}>
                         {selectedCode ? (
                             <DetailMetier romeCode={selectedCode} />
                         ) : (
                             <div className={`${styles['wiki-metier-empty']} nb-text-dim`}>
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
