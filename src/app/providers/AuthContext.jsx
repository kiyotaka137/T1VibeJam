import React, { createContext, useContext, useState } from "react";

// Создаем контекст
const AuthContext = createContext(null);

// Провайдер (Обертка)
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);

  // Заглушки функций, чтобы LoginPage не ломалась
  const login = async (email, password) => {
    console.log("Mock Login called", email);
    setUser({ email, role: 'hr' });
  };

  const signup = async (data) => {
    console.log("Mock Signup called", data);
    setUser({ email: data.email, role: data.role });
  };

  const logout = () => {
    setUser(null);
  };

  // Значения, которые доступны в любом компоненте через useAuth()
  const value = {
    user,
    login,
    signup,
    logout
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Хук для использования
export const useAuth = () => {
  return useContext(AuthContext);
};