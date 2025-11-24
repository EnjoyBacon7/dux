import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "./contexts/useAuth";

const RequireAuth: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { user, loading } = useAuth();

    if (loading) {
        return (
            <div style={{ maxWidth: 600, margin: "2rem auto", padding: 24, textAlign: "center" }}>
                <p>Loading...</p>
            </div>
        );
    }

    if (!user) {
        return <Navigate to="/login" replace />;
    }

    return <>{children}</>;
};

export default RequireAuth;
