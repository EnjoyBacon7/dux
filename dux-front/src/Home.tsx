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
            <div style={{ maxWidth: 600, margin: "2rem auto", padding: 24, textAlign: "center" }}>
                <p>Loading...</p>
            </div>
        );
    }

    if (!user) {
        return null;
    }

    return (
        <div style={{ maxWidth: 600, margin: "2rem auto", padding: 24, border: "1px solid #eee", borderRadius: 8 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
                <h1 style={{ margin: 0 }}>Welcome to Dux</h1>
                <button
                    onClick={signOut}
                    style={{
                        padding: "8px 16px",
                        background: "#d32f2f",
                        color: "white",
                        border: "none",
                        borderRadius: 4,
                        fontWeight: 600,
                        cursor: "pointer"
                    }}>
                    Logout
                </button>
            </div>

            <div style={{ padding: 20, background: "#f5f5f5", borderRadius: 8, marginBottom: 24 }}>
                <p style={{ margin: 0, fontSize: 18 }}>
                    Logged in as: <strong>{user.username}</strong>
                </p>
            </div>

            <div style={{ marginTop: 24 }}>
                <p style={{ color: "#666" }}>
                    You are now authenticated and can access protected features.
                </p>
            </div>
        </div>
    );
};

export default Home;
