import Upload from "./Upload";
import AuthPage from "./AuthPage";
import Home from "./Home";
import LinkedInCallback from "./LinkedInCallback";
import PrivacyPolicy from "./PrivacyPolicy";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { LanguageProvider } from "./contexts/LanguageContext";
import RequireAuth from "./RequireAuth";

function App() {
    return (
        <BrowserRouter>
            <LanguageProvider>
                <AuthProvider>
                    <Routes>
                        <Route path="/login" element={<AuthPage />} />
                        <Route path="/upload" element={<RequireAuth><Upload /></RequireAuth>} />
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
