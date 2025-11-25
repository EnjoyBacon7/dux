import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./contexts/useAuth";
import Header from "./components/Header";
import AccountCard from "./components/AccountCard";

const Home: React.FC = () => {
    const navigate = useNavigate();
    const { user, loading } = useAuth();

    useEffect(() => {
        if (!loading && !user) {
            navigate("/login");
        }
    }, [user, loading, navigate]);

    if (loading) {
        return (
            <div className="nb-page nb-card nb-center nb-card--muted">
                <p>Loading...</p>
            </div>
        );
    }

    if (!user) {
        return null;
    }

    return (
        <>
            <Header />
            <div className="nb-page nb-stack">
                <AccountCard 
                    username={user.username}
                    firstName={user.first_name}
                    lastName={user.last_name}
                    title={user.title}
                    profilePicture={user.profile_picture}
                />
                <div className="nb-card">
                    <h1 style={{ margin: '0 0 1rem 0' }}>Welcome to Dux</h1>
                    <p className="nb-text-dim">You are now authenticated and can access protected features.</p>
                </div>
            </div>
        </>
    );
};

export default Home;
