// src/services/api.js

// Оставляем пустым, так как используем Proxy в vite.config.js
const API_URL = ""; 

export const api = {
  getToken: () => localStorage.getItem("auth_token"),
  
  // Если нужно, можно добавить для внутренних вызовов
  getInternalKey: () => "my-secret-internal-key", 

  async request(endpoint, method = "GET", body = null, isInternal = false) {
    const headers = {
      "Content-Type": "application/json",
    };

    if (isInternal) {
      headers["X-Internal-API-Key"] = this.getInternalKey();
    } else {
      const token = this.getToken();
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
    }

    const config = {
      method,
      headers,
    };

    if (body) {
      config.body = JSON.stringify(body);
    }

    try {
      const response = await fetch(`${API_URL}${endpoint}`, config);

      // 1. Сначала обрабатываем статус 401 (Нет доступа / Токен протух)
      if (response.status === 401) {
        console.warn("Auth error: 401 Unauthorized");
        localStorage.removeItem("auth_token");
        // Опционально: редирект на логин
        // window.location.href = "/"; 
        throw new Error("Ошибка авторизации. Пожалуйста, войдите снова.");
      }

      // 2. Читаем ответ как текст, чтобы не упасть, если придет пустое тело
      const text = await response.text();
      let data;
      try {
        data = text ? JSON.parse(text) : {};
      } catch (err) {
        // Если вернулся не JSON (например, HTML страница ошибки от nginx)
        throw new Error(`Server error: ${response.status} ${response.statusText}`);
      }

      // 3. Если статус ответа не OK (не 2xx), кидаем ошибку с сообщением от бэка
      if (!response.ok) {
        throw new Error(data.message || `Ошибка ${response.status}`);
      }

      return data;
    } catch (error) {
      console.error("API Request Failed:", error);
      throw error;
    }
  },

  get(endpoint) {
    return this.request(endpoint, "GET");
  },

  post(endpoint, body) {
    return this.request(endpoint, "POST", body);
  }
};