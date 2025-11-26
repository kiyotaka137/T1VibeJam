import React, { useState, useEffect } from "react";
// Проверьте, что пути соответствуют вашей структуре!
import { LoginPage } from "../pages/LoginPage/LoginPage"; 
import { HRDashboard } from "../pages/HRDashboard/HRDashboard";
import { InterviewRoom } from "../pages/InterviewRoom/InterviewRoom";
import { AuthProvider } from "./providers/AuthContext"; 

export default function App() {
  const [currentPage, setCurrentPage] = useState("login"); // 'login', 'hr', 'interview'
  const [inviteToken, setInviteToken] = useState(null);

  useEffect(() => {
    // Проверяем, есть ли инвайт в ссылке (например: http://localhost:3000/?invite=abc-123)
    const params = new URLSearchParams(window.location.search);
    const token = params.get("invite");
    if (token) {
      setInviteToken(token);
      setCurrentPage("interview");
    }
  }, []);

  // Эта функция передается в LoginPage
  const handleLoginSuccess = (token) => {
    console.log("Переход на HR Dashboard");
    // В реальном app токен сохраняет AuthProvider, здесь для простоты:
    localStorage.setItem("auth_token", token || "mock_hr_token"); 
    setCurrentPage("hr");
  };

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    setInviteToken(null);
    setCurrentPage("login");
    // Очищаем URL от инвайта
    window.history.replaceState(null, "", "/");
  };

  const handleStartInterview = () => {
    // Режим демо для HR (без токена инвайта)
    setInviteToken(null);
    setCurrentPage("interview");
  };

  return (
    // ВАЖНО: AuthProvider должен оборачивать всё
    <AuthProvider>
      {currentPage === "login" && (
        <LoginPage onLogin={handleLoginSuccess} />
      )}

      {currentPage === "hr" && (
        <HRDashboard
          onNavigateToInterview={handleStartInterview}
          onLogout={handleLogout}
        />
      )}

      {currentPage === "interview" && (
        <InterviewRoom 
          onExit={handleLogout} 
          inviteToken={inviteToken} 
        />
      )}
    </AuthProvider>
  );
}