import React, { useState } from "react";
// Проверьте, что пути соответствуют вашей структуре!
import { LoginPage } from "../pages/LoginPage/LoginPage"; 
import { HRDashboard } from "../pages/HRDashboard/HRDashboard";
import { InterviewRoom } from "../pages/InterviewRoom/InterviewRoom";
import { AuthProvider } from "./providers/AuthContext"; 

export default function App() {
  const [currentPage, setCurrentPage] = useState("login"); // 'login', 'hr', 'interview'

  // Эта функция передается в LoginPage
  const handleLoginSuccess = () => {
    console.log("Переход на HR Dashboard");
    setCurrentPage("hr");
  };

  const handleLogout = () => {
    setCurrentPage("login");
  };

  const handleStartInterview = () => {
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
        <InterviewRoom onExit={handleLogout} />
      )}
    </AuthProvider>
  );
}