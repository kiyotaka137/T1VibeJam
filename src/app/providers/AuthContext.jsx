import React, { createContext, useContext, useMemo, useState } from "react";
import { createHttpClient } from "../../shared/api/http.js";
import { createAuthApi } from "../../shared/api/auth.js";

const AuthContext = createContext(null);

const AUTH_BASE_URL = import.meta.env.VITE_AUTH_BASE_URL;

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("access_token"));
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem("me");
    return raw ? JSON.parse(raw) : null;
  });

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("access_token");
    localStorage.removeItem("me");
  };

  const http = useMemo(
    () =>
      createHttpClient({
        baseUrl: AUTH_BASE_URL,
        getToken: () => token,
        onUnauthorized: logout,
      }),
    [token]
  );

  const authApi = useMemo(() => createAuthApi(http), [http]);

  const api = useMemo(() => {
    return {
      user,
      token,

      async login(email, password) {
        const data = await authApi.login({ email, password });
        setToken(data.access_token);
        localStorage.setItem("access_token", data.access_token);

        const me = await createAuthApi(
          createHttpClient({
            baseUrl: AUTH_BASE_URL,
            getToken: () => data.access_token,
          })
        ).me();

        setUser(me);
        localStorage.setItem("me", JSON.stringify(me));
        return me;
      },

      async signup({ email, password, name, role }) {
        const data = await authApi.signup({ email, password, name, role });
        setToken(data.access_token);
        localStorage.setItem("access_token", data.access_token);

        const me = await createAuthApi(
          createHttpClient({
            baseUrl: AUTH_BASE_URL,
            getToken: () => data.access_token,
          })
        ).me();

        setUser(me);
        localStorage.setItem("me", JSON.stringify(me));
        return me;
      },

      logout,
    };
  }, [authApi, token, user]);

  return <AuthContext.Provider value={api}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider />");
  return ctx;
}
