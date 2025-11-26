import React, { createContext, useContext, useState, useEffect } from "react";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Функция для получения данных пользователя по токену
  const fetchMe = async (token) => {
    try {
      const response = await fetch("/v1/users/me", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) throw new Error("Failed to fetch user");

      const userData = await response.json();
      // userData = {id, email, name, role, created_at}
      setUser(userData);
    } catch (error) {
      console.error("Auth check failed:", error);
      logout(); // Если токен протух — выходим
    } finally {
      setLoading(false);
    }
  };

  // Проверка авторизации при загрузке страницы
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      fetchMe(token);
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email, password) => {
    // 1. Получаем токен
    const response = await fetch("/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Ошибка входа");
    }

    const data = await response.json(); // { access_token: "..." }
    localStorage.setItem("access_token", data.access_token);

    // 2. Загружаем данные пользователя
    await fetchMe(data.access_token);
  };

  const signup = async ({ email, password, name, role }) => {
    // 1. Регистрация
    const response = await fetch("/v1/auth/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, name, role }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Ошибка регистрации");
    }

    const data = await response.json(); // { access_token: "..." }
    localStorage.setItem("access_token", data.access_token);

    // 2. Загружаем данные пользователя
    await fetchMe(data.access_token);
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    setUser(null);
  };

  const value = {
    user,
    login,
    signup,
    logout,
    isAuthenticated: !!user,
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);