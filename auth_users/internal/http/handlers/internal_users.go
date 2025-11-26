package handlers

import (
	"errors"
	"net/http"

	"auth_users/internal/service"
)

type InternalUsersHandler struct {
	auth *service.AuthService
}

func NewInternalUsersHandler(auth *service.AuthService) *InternalUsersHandler {
	return &InternalUsersHandler{auth: auth}
}

type precreateReq struct {
	Email string `json:"email"`
	Name  string `json:"name"`
}

func (h *InternalUsersHandler) PrecreateCandidate(w http.ResponseWriter, r *http.Request) {
	var req precreateReq
	if err := decodeJSON(w, r, &req); err != nil {
		return
	}
	u, err := h.auth.PrecreateCandidate(r.Context(), req.Email, req.Name)
	if err != nil {
		if errors.Is(err, service.ErrValidation) {
			writeError(w, http.StatusBadRequest, "bad_request", err.Error())
			return
		}
		if errors.Is(err, service.ErrEmailTaken) {
			writeError(w, http.StatusConflict, "email_taken", "email already used")
			return
		}
		writeError(w, http.StatusInternalServerError, "internal_error", err.Error())
		return
	}
	writeJSON(w, http.StatusOK, u)
}
