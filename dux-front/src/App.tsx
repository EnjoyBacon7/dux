import AuthPage from "./AuthPage";
import Home from "./Home";
import Settings from "./Settings";
import JobSearch from "./JobSearch";
import ProfileSetup from "./ProfileSetup";
import LinkedInCallback from "./LinkedInCallback";
import PrivacyPolicy from "./PrivacyPolicy";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { LanguageProvider } from "./contexts/LanguageContext";
import RequireAuth from "./RequireAuth";
import { useEffect } from "react";

// Initialize theme on app startup
const applyTheme = (selectedTheme: 'light' | 'dark' | 'auto') => {
    const root = document.documentElement;
    if (selectedTheme === 'auto') {
        root.removeAttribute('data-theme');
    } else {
        root.setAttribute('data-theme', selectedTheme);
    }
};

function App() {
    // Apply saved theme on mount
    useEffect(() => {
        const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | 'auto' || 'auto';
        applyTheme(savedTheme);
    }, []);

    return (
        <BrowserRouter>
            <LanguageProvider>
                <AuthProvider>
                    <Routes>
                        <Route path="/login" element={<AuthPage />} />
                        <Route path="/setup" element={<RequireAuth><ProfileSetup /></RequireAuth>} />
                        <Route path="/settings" element={<RequireAuth><Settings /></RequireAuth>} />
                        <Route path="/jobs" element={<RequireAuth><JobSearch /></RequireAuth>} />
                        <Route path="/linkedin/callback" element={<LinkedInCallback />} />
                        <Route path="/privacy" element={<PrivacyPolicy />} />
                        <Route path="/" element={<RequireAuth><Home /></RequireAuth>} />
                    </Routes>
                </AuthProvider>
            </LanguageProvider>
        </BrowserRouter>
    );
}

export default App;
