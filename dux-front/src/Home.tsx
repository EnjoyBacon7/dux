import React, { useState, useCallback } from "react";
import { useAuth } from "./contexts/useAuth";
import { Header, AccountCard, JobOffersCard, WelcomeCard, CVUploadForm, CVPreview, CVScoreCard } from "./components";
import "./styles/home.css";

const Home: React.FC = () => {
    const { user, checkAuth } = useAuth();
    const [cvRefreshTrigger, setCvRefreshTrigger] = useState(0);

    const handleCvUploadSuccess = useCallback(async () => {
        await checkAuth();
        // Increment trigger to refresh CVScoreCard
        setCvRefreshTrigger(prev => prev + 1);
    }, [checkAuth]);

    if (!user) return null; // Guard: page is wrapped by RequireAuth

    const hasCv = Boolean(user.cv_filename);

    return (
        <>
            <Header />
            <main className="nb-page home-container">
                <div className="home-grid">
                    <WelcomeCard />
                    <AccountCard
                        username={user.username}
                        firstName={user.first_name}
                        lastName={user.last_name}
                        title={user.title}
                        profilePicture={user.profile_picture}
                    />
                    <CVUploadForm onSuccess={handleCvUploadSuccess} />
                    <CVScoreCard hasCv={hasCv} refreshTrigger={cvRefreshTrigger} />
                    <CVPreview hasCV={hasCv} cvFilename={user.cv_filename} />
                    <JobOffersCard />
                </div>
            </main>
        </>
    );
};

export default Home;
