package handlers

import (
	"net/http"

	"auth_users/internal/http/middleware"
	"auth_users/internal/service"
)

type UsersHandler struct {
	auth *service.AuthService
}

func NewUsersHandler(auth *service.AuthService) *UsersHandler {
	return &UsersHandler{auth: auth}
}

func (h *UsersHandler) Me(w http.ResponseWriter, r *http.Request) {
	uid := middleware.UserID(r)
	if uid == "" {
		writeError(w, http.StatusUnauthorized, "unauthorized", "missing user in context")
		return
	}
	u, err := h.auth.Me(r.Context(), uid)
	if err != nil {
		writeError(w, http.StatusNotFound, "not_found", "user not found")
		return
	}
	writeJSON(w, http.StatusOK, u)
}
