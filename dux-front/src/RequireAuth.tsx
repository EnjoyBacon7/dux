import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "./contexts/useAuth";

const RequireAuth: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { user, loading } = useAuth();
    const location = useLocation();

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

    // Redirect to setup if CV is missing, unless already on setup page
    if (!user.cv_filename && location.pathname !== '/setup') {
        return <Navigate to="/setup" replace />;
    }
    // Redirect to home if CV exists and user tries to access setup page
    if (user.cv_filename && location.pathname === '/setup') {
        return <Navigate to="/" replace />;
    }
    return <>{children}</>;
};

export default RequireAuth;