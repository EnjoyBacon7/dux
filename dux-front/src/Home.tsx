import React from "react";
import { useAuth } from "./contexts/useAuth";
import { Header, AccountCard, JobOffersCard, WelcomeCard, CVUploadForm, CVPreview } from "./components";
import "./styles/home.css";

const Home: React.FC = () => {
    const { user, checkAuth } = useAuth();

    if (!user) return null; // Guard: page is wrapped by RequireAuth

    const hasCv = Boolean(user.cv_filename);

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
                    <WelcomeCard />
                    <CVUploadForm onSuccess={checkAuth} />
                    <CVPreview hasCV={hasCv} cvFilename={user.cv_filename} />
                    <JobOffersCard />
                </div>
            </div>
        </>
    );
};

export default Home;
