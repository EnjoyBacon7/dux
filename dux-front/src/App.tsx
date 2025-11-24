import Upload from "./Upload";
import AuthPage from "./AuthPage";
import Home from "./Home";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import RequireAuth from "./RequireAuth";

function App() {
    return (
        <BrowserRouter>
            <AuthProvider>
                <Routes>
                    <Route path="/login" element={<AuthPage />} />
                    <Route path="/upload" element={<RequireAuth><Upload /></RequireAuth>} />
                    <Route path="/" element={<RequireAuth><Home /></RequireAuth>} />
                </Routes>
            </AuthProvider>
        </BrowserRouter>
    );
}

export default App;
