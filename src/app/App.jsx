import React from "react";
import { Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./providers/AuthContext.jsx";

import { LoginPage } from "../pages/LoginPage/LoginPage.jsx";
import { HRDashboard } from "../pages/HRDashboard/HRDashboard.jsx";
import { InterviewRoom } from "../pages/InterviewRoom/InterviewRoom.jsx";

function RequireHR({ children }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== "hr") return <Navigate to="/login" replace />;
  return children;
}

function AppRoutes() {
  const { loginAsHR, logout } = useAuth();
  const nav = useNavigate();

  return (
    <Routes>
      <Route
        path="/login"
        element={
          <LoginPage
            onLogin={() => {
              loginAsHR();
              nav("/hr");
            }}
          />
        }
      />

      <Route
        path="/hr"
        element={
          <RequireHR>
            <HRDashboard
              onLogout={() => {
                logout();
                nav("/login");
              }}
              onNavigateToInterview={() => nav("/interview")}
            />
          </RequireHR>
        }
      />

      <Route
        path="/interview"
        element={<InterviewRoom onExit={() => nav("/hr")} />}
      />

      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}
