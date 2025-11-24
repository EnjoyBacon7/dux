import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./contexts/useAuth";

const Home: React.FC = () => {
    const navigate = useNavigate();
    const { user, loading, signOut } = useAuth();

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
        <div className="nb-page nb-stack">
            <div className="nb-card">
                <div className="nb-spread nb-gap-sm" style={{ marginBottom: '1rem' }}>
                    <h1 style={{ margin: 0 }}>Welcome to Dux</h1>
                    <button onClick={signOut} className="nb-btn nb-btn--danger">Logout</button>
                </div>
                <div className="nb-card nb-card--muted" style={{ padding: '1rem', marginBottom: '1rem' }}>
                    <p style={{ margin: 0, fontSize: '1.1rem' }}>
                        Logged in as: <strong>{user.username}</strong>
                    </p>
                </div>
                <p className="nb-text-dim">You are now authenticated and can access protected features.</p>
            </div>
        </div>
    );
};

export default Home;
