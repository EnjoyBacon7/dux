import React, { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import { Header } from "./components";
import { useLanguage } from "./contexts/useLanguage";
import styles from "./styles/AdvisorChat.module.css";

type Intent = "orientation" | "cover_letter" | "cv_tips";

type FavouriteJobItem = {
  jobId: string;
  intitule: string;
  entreprise_nom?: string | null;
  romeCode?: string | null;
  addedAt?: string | null;
};

type ConversationItem = {
  id: number;
  title: string | null;
  updatedAt: string | null;
};

type MessageItem = {
  role: "user" | "assistant";
  content: string;
  createdAt?: string | null;
};

type AdvisorContext = {
  hasCv: boolean;
  latestEvaluation: Record<string, unknown> | null;
  favouriteJobs: FavouriteJobItem[];
};

const INTENTS: { value: Intent; key: string }[] = [
  { value: "orientation", key: "advisor.intent.orientation" },
  { value: "cover_letter", key: "advisor.intent.cover_letter" },
  { value: "cv_tips", key: "advisor.intent.cv_tips" },
];

export default function OrientationAdvisor() {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const jobIdFromUrl = searchParams.get("jobId");
  const conversationIdFromUrl = searchParams.get("conversationId");

  const [context, setContext] = useState<AdvisorContext | null>(null);
  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [intent, setIntent] = useState<Intent>(jobIdFromUrl ? "cover_letter" : "orientation");
  const [selectedJobId, setSelectedJobId] = useState<string | null>(jobIdFromUrl);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [renameId, setRenameId] = useState<number | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const renameCancelRef = useRef<boolean>(false);

  const fetchContext = useCallback(async () => {
    const res = await fetch("/api/advisor/context", { credentials: "include" });
    if (!res.ok) throw new Error("Failed to load context");
    const data = await res.json();
    setContext({
      hasCv: data.hasCv ?? false,
      latestEvaluation: data.latestEvaluation ?? null,
      favouriteJobs: Array.isArray(data.favouriteJobs) ? data.favouriteJobs : [],
    });
  }, []);

  const fetchConversations = useCallback(async () => {
    const res = await fetch("/api/advisor/conversations", { credentials: "include" });
    if (!res.ok) throw new Error("Failed to load conversations");
    const data = await res.json();
    setConversations(Array.isArray(data) ? data : []);
  }, []);

  const fetchConversation = useCallback(async (id: number) => {
    const res = await fetch(`/api/advisor/conversations/${id}`, { credentials: "include" });
    if (!res.ok) throw new Error("Failed to load conversation");
    const data = await res.json();
    setMessages(
      (data.messages ?? []).map((m: { role: string; content: string; createdAt?: string }) => ({
        role: m.role as "user" | "assistant",
        content: m.content,
        createdAt: m.createdAt,
      }))
    );
    setCurrentConversationId(id);
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function init() {
      setLoading(true);
      setError(null);
      try {
        await Promise.all([fetchContext(), fetchConversations()]);
        if (cancelled) return;
        if (conversationIdFromUrl) {
          const id = parseInt(conversationIdFromUrl, 10);
          if (!Number.isNaN(id)) await fetchConversation(id);
        } else {
          setCurrentConversationId(null);
          setMessages([]);
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Error");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    init();
    return () => {
      cancelled = true;
    };
  }, [conversationIdFromUrl, fetchContext, fetchConversations, fetchConversation]);

  /* Scroll chat to bottom so the latest messages are visible */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleBack = () => navigate("/profile-hub");
  const handleNewChat = () => {
    setCurrentConversationId(null);
    setMessages([]);
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.delete("conversationId");
      return next;
    });
  };

  const handleSelectConversation = (id: number) => {
    setRenameId(null);
    setDeleteConfirmId(null);
    fetchConversation(id);
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set("conversationId", String(id));
      return next;
    });
  };

  const handleRenameStart = (conv: ConversationItem, e: React.MouseEvent) => {
    e.stopPropagation();
    setRenameId(conv.id);
    setRenameValue(conv.title || "");
  };
  const handleRenameSubmit = async (id: number) => {
    const title = renameValue.trim();
    const res = await fetch(`/api/advisor/conversations/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ title: title || "" }),
    });
    if (res.ok) {
      setConversations((prev) =>
        prev.map((c) => (c.id === id ? { ...c, title: title || "" } : c))
      );
      setRenameId(null);
    }
  };
  const handleRenameKeyDown = (id: number, e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleRenameSubmit(id);
    if (e.key === "Escape") {
      renameCancelRef.current = true;
      setRenameId(null);
    }
  };
  const handleRenameBlur = (id: number) => {
    if (renameCancelRef.current) {
      renameCancelRef.current = false;
      setRenameId(null);
      return;
    }
    handleRenameSubmit(id);
  };

  const handleDeleteClick = (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    setDeleteConfirmId(id);
  };
  const handleDeleteConfirm = async (id: number) => {
    const res = await fetch(`/api/advisor/conversations/${id}`, {
      method: "DELETE",
      credentials: "include",
    });
    if (res.ok) {
      setConversations((prev) => prev.filter((c) => c.id !== id));
      setDeleteConfirmId(null);
      if (currentConversationId === id) {
        setCurrentConversationId(null);
        setMessages([]);
        setSearchParams((prev) => {
          const next = new URLSearchParams(prev);
          next.delete("conversationId");
          return next;
        });
      }
    }
  };

  const handleSend = async (optionalMessage?: string) => {
    const text = (optionalMessage ?? input).trim();
    if (!text || sending) return;
    if (!optionalMessage) setInput("");
    setSending(true);
    setError(null);
    const userMsg: MessageItem = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    const history = [...messages, userMsg].slice(-20).map((m) => ({ role: m.role, content: m.content }));
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);
    try {
      const body: Record<string, unknown> = {
        message: text,
        conversationHistory: history,
        context: { intent, jobId: intent === "cover_letter" ? selectedJobId : undefined },
      };
      if (currentConversationId) body.conversationId = currentConversationId;
      const res = await fetch("/api/advisor/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Send failed");
      }
      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let streamError: string | null = null;
      if (!reader) throw new Error("No response body");
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6)) as { content?: string; done?: boolean; conversationId?: number; error?: string };
              if (data.error) {
                streamError = data.error;
                break;
              }
              if (typeof data.content === "string") {
                setMessages((prev) => {
                  const next = [...prev];
                  const last = next[next.length - 1];
                  if (last && last.role === "assistant") {
                    next[next.length - 1] = { ...last, content: last.content + data.content };
                  }
                  return next;
                });
              }
              if (data.done && data.conversationId != null) {
                const convId = data.conversationId;
                if (currentConversationId === null && convId) {
                  setCurrentConversationId(convId);
                  setConversations((prev) => [
                    { id: convId, title: text.slice(0, 50) + (text.length > 50 ? "..." : ""), updatedAt: new Date().toISOString() },
                    ...prev,
                  ]);
                  setSearchParams((prev) => {
                    const next = new URLSearchParams(prev);
                    next.set("conversationId", String(convId));
                    return next;
                  });
                } else if (currentConversationId && convId) {
                  setConversations((prev) =>
                    prev.map((c) => (c.id === convId ? { ...c, updatedAt: new Date().toISOString() } : c))
                  );
                }
              }
            } catch (parseErr) {
              if (parseErr instanceof Error && parseErr.message !== "Send failed") {
                streamError = parseErr.message;
                break;
              }
            }
          }
        }
        if (streamError) break;
      }
      if (streamError) {
        setError(streamError);
        setMessages((prev) => prev.slice(0, -2));
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Send failed");
      setMessages((prev) => prev.slice(0, -2));
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return (
      <>
        <Header />
        <main className={styles["advisor-container"]}>
          <div className={styles["advisor-loading"]}>{t("common.loading") || "Loading..."}</div>
        </main>
      </>
    );
  }

  return (
    <>
      <Header />
      <main className={styles["advisor-container"]}>
        <aside className={styles["advisor-sidebar"]}>
          <div className={styles["advisor-sidebar-header"]}>
            <button type="button" className={styles["advisor-new-chat-btn"]} onClick={handleNewChat}>
              + {t("advisor.new_chat")}
            </button>
          </div>
          <div className={styles["advisor-conversations-list"]}>
            {conversations.length === 0 ? (
              <div className={styles["advisor-empty-sidebar"]}>
                {t("advisor.no_conversations")}
              </div>
            ) : (
              conversations.map((conv) => (
                <div
                  key={conv.id}
                  className={`${styles["advisor-conv-item"]} ${currentConversationId === conv.id ? styles["advisor-conv-item--active"] : ""}`}
                  onClick={() => handleSelectConversation(conv.id)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => e.key === "Enter" && handleSelectConversation(conv.id)}
                >
                  {renameId === conv.id ? (
                    <input
                      type="text"
                      className={styles["advisor-rename-input"]}
                      value={renameValue}
                      onChange={(e) => setRenameValue(e.target.value)}
                      onBlur={() => handleRenameBlur(conv.id)}
                      onKeyDown={(e) => handleRenameKeyDown(conv.id, e)}
                      onClick={(e) => e.stopPropagation()}
                      autoFocus
                    />
                  ) : (
                    <>
                      <span className={styles["advisor-conv-item-title"]} title={conv.title || undefined}>
                        {conv.title || t("advisor.untitled")}
                      </span>
                      <span className={styles["advisor-conv-item-date"]}>
                        {conv.updatedAt ? new Date(conv.updatedAt).toLocaleDateString() : ""}
                      </span>
                      <div className={styles["advisor-conv-item-actions"]} onClick={(e) => e.stopPropagation()}>
                        <button type="button" onClick={(e) => handleRenameStart(conv, e)} title={t("advisor.rename")} aria-label={t("advisor.rename")}>
                          ✏️
                        </button>
                        <button type="button" onClick={(e) => handleDeleteClick(conv.id, e)} title={t("advisor.delete")} aria-label={t("advisor.delete")}>
                          🗑️
                        </button>
                      </div>
                      {deleteConfirmId === conv.id && (
                        <div className={styles["advisor-delete-confirm"]} onClick={(e) => e.stopPropagation()}>
                          <p>{t("advisor.delete_confirm")}</p>
                          <div className={styles["advisor-delete-confirm-btns"]}>
                            <button type="button" className="nb-btn nb-btn--accent" onClick={() => handleDeleteConfirm(conv.id)}>
                              {t("common.yes") || "Yes"}
                            </button>
                            <button type="button" className="nb-btn nb-btn--ghost" onClick={() => setDeleteConfirmId(null)}>
                              {t("common.cancel") || "Cancel"}
                            </button>
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
              ))
            )}
          </div>
        </aside>
        <div className={styles["advisor-main"]}>
          <div className={styles["advisor-header"]}>
            <button type="button" className={styles["advisor-back-btn"]} onClick={handleBack}>
              ← {t("profile_hub.back") || "Back to Profile Hub"}
            </button>
            <h1 className={styles["advisor-title"]}>{t("profile_hub.advisor")}</h1>
          </div>
          {context?.hasCv && context.latestEvaluation && (
            <div className={styles["advisor-cv-notice"]}>
              {t("advisor.cv_feedback") || "You have CV feedback. The advisor can use it for orientation and CV tips."}
            </div>
          )}
          <div className={styles["advisor-messages-wrapper"]}>
            <div className={styles["advisor-messages"]}>
            {messages.length === 0 ? (
              <div className={styles["advisor-empty-state"]}>
                <div className={styles["advisor-empty-state-inner"]}>
                  <h2 className={styles["advisor-empty-state-title"]}>{t("profile_hub.advisor")}</h2>
                  <p className={styles["advisor-empty-state-desc"]}>{t("profile_hub.advisor_desc")}</p>
                  <div className={styles["advisor-intent-tabs"]}>
                    {INTENTS.map(({ value, key }) => (
                      <button
                        key={value}
                        type="button"
                        className={`${styles["advisor-intent-tab"]} ${intent === value ? styles["advisor-intent-tab--active"] : ""}`}
                        onClick={() => setIntent(value)}
                      >
                        {t(key)}
                      </button>
                    ))}
                  </div>
                  {intent === "cover_letter" && (
                    <div className={styles["advisor-job-picker"]}>
                      <label htmlFor="advisor-job-select">{t("advisor.select_job")}</label>
                      <select
                        id="advisor-job-select"
                        className="nb-input"
                        value={selectedJobId ?? ""}
                        onChange={(e) => setSelectedJobId(e.target.value || null)}
                      >
                        <option value="">—</option>
                        {jobIdFromUrl && !(context?.favouriteJobs ?? []).some((j) => j.jobId === jobIdFromUrl) && (
                          <option value={jobIdFromUrl}>{t("advisor.current_job")}</option>
                        )}
                        {(context?.favouriteJobs ?? []).map((j) => (
                          <option key={j.jobId} value={j.jobId}>
                            {j.intitule} {j.entreprise_nom ? `@ ${j.entreprise_nom}` : ""}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}
                  <div className={styles["advisor-suggestions"]}>
                    {(["advisor.suggest_1", "advisor.suggest_2", "advisor.suggest_3", "advisor.suggest_4"] as const).map((key) => (
                      <button
                        key={key}
                        type="button"
                        className={styles["advisor-suggestion-btn"]}
                        onClick={() => handleSend(t(key))}
                        disabled={sending}
                      >
                        {t(key)}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : null}
            {messages.length > 0 && (
              <div className={styles["advisor-context-pill"]}>
                <div className={styles["advisor-context-pill-line"]}>
                  <span className={styles["advisor-context-pill-label"]}>{t("advisor.intent_label")}:</span>{" "}
                  {t(INTENTS.find((x) => x.value === intent)?.key ?? "advisor.intent.orientation")}
                </div>
                {intent === "cover_letter" && selectedJobId && (
                  <div className={styles["advisor-context-pill-line"]}>
                    <span className={styles["advisor-context-pill-label"]}>{t("advisor.job_details")}:</span>{" "}
                    {(() => {
                      const job = (context?.favouriteJobs ?? []).find((j) => j.jobId === selectedJobId);
                      if (job) return `${job.intitule}${job.entreprise_nom ? ` @ ${job.entreprise_nom}` : ""}`;
                      if (selectedJobId === jobIdFromUrl) return t("advisor.current_job");
                      return selectedJobId;
                    })()}
                  </div>
                )}
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`${styles["advisor-msg"]} ${m.role === "user" ? styles["advisor-msg--user"] : styles["advisor-msg--assistant"]}`}>
                <div className={styles["advisor-msg-content"]}>
                  {m.role === "assistant" ? <ReactMarkdown>{m.content}</ReactMarkdown> : m.content}
                </div>
                {m.createdAt && <div className={styles["advisor-msg-time"]}>{new Date(m.createdAt).toLocaleString()}</div>}
              </div>
            ))}
            <div ref={messagesEndRef} aria-hidden="true" />
            </div>
          </div>
          {error && <div className={styles["advisor-error"]}>{error}</div>}
          <div className={styles["advisor-input-zone"]}>
            <div className={styles["advisor-input-area"]}>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), handleSend())}
              placeholder={t("advisor.placeholder") || "Type your message..."}
              rows={2}
              disabled={sending}
            />
            <button type="button" className={styles["advisor-send-btn"]} onClick={() => handleSend()} disabled={sending || !input.trim()}>
              {sending ? (t("common.loading") || "Sending...") : (t("advisor.send") || "Send")}
            </button>
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
