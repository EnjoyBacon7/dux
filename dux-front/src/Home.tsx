import React, { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./contexts/useAuth";
import { useLanguage } from "./contexts/useLanguage";
import { Header, AccountCard, JobOffersCard } from "./components";
import "./styles/home.css";

const Home: React.FC = () => {
    const navigate = useNavigate();
    const { user } = useAuth();
    const { t } = useLanguage();
    const fileInputRef = useRef<HTMLInputElement | null>(null);
    const [uploading, setUploading] = useState(false);
    const [success, setSuccess] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    if (!user) return null; // Guard: page is wrapped by RequireAuth

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setSuccess(null);
        setError(null);
        const file = fileInputRef.current?.files?.[0];
        if (!file) {
            setError("Please select a file to upload.");
            return;
        }
        setUploading(true);
        try {
            const formData = new FormData();
            formData.append("file", file);
            const res = await fetch("/api/profile/upload", {
                method: "POST",
                body: formData,
            });
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || "Upload failed");
            }
            const data = await res.json();
            setSuccess(data.message || "File uploaded successfully!");
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : "Upload failed";
            setError(message);
        } finally {
            setUploading(false);
        }
    };

    return (
        <>
            <Header />
            <div className="nb-page">
                <AccountCard
                    username={user.username}
                    firstName={user.first_name}
                    lastName={user.last_name}
                    title={user.title}
                    profilePicture={user.profile_picture}
                />

                <div className="home-grid">
                    {/* Welcome Card */}
                    <div className="nb-card home-card">
                        <h1 className="home-title">{t('home.welcome')}</h1>
                        <p className="nb-text-dim">{t('home.authenticated')}</p>
                        <div className="home-actions">
                            <button
                                onClick={() => navigate('/jobs')}
                                className="nb-btn"
                            >
                                {t('jobs.title')}
                            </button>
                        </div>
                    </div>

                    {/* Upload Card */}
                    <div className="nb-card home-card">
                        <h2 className="home-card-title">{t('upload.title')}</h2>
                        <form className="nb-form home-upload-form" onSubmit={handleSubmit}>
                            <input
                                type="file"
                                ref={fileInputRef}
                                className="nb-file"
                                disabled={uploading}
                            />
                            <button
                                type="submit"
                                className={`nb-btn ${uploading ? 'nb-btn--ghost' : 'nb-btn--accent'}`}
                                disabled={uploading}
                            >
                                {uploading ? t('upload.uploading') : t('upload.button')}
                            </button>
                        </form>
                        {success && <div className="nb-alert nb-alert--success nb-mt">{success}</div>}
                        {error && <div className="nb-alert nb-alert--danger nb-mt">{error}</div>}
                    </div>

                    {/* Job Offers Carousel Card */}
                    <JobOffersCard />
                </div>
            </div>
        </>
    );
};

export default Home;
