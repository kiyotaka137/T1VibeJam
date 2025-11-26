export function createAuthApi(http) {
  return {
    signup: (payload) => http.post("/v1/auth/signup", payload),
    login: (payload) => http.post("/v1/auth/login", payload),
    me: () => http.get("/v1/users/me"),
  };
}
