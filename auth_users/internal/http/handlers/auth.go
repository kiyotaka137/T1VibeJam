package handlers

import (
	"encoding/json"
	"errors"
	"net/http"

	types "auth_users/internal/models"
	"auth_users/internal/service"
)

type AuthHandler struct {
	auth *service.AuthService
}

func NewAuthHandler(auth *service.AuthService) *AuthHandler {
	return &AuthHandler{auth: auth}
}

type signupReq struct {
	Email    string `json:"email"`
	Password string `json:"password"`
	Name     string `json:"name"`
	Role     string `json:"role"`
}

type loginReq struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

type authResp struct {
	AccessToken string     `json:"access_token"`
	TokenType   string     `json:"token_type"`
	User        types.User `json:"user"`
}

func (h *AuthHandler) Signup(w http.ResponseWriter, r *http.Request) {
	var req signupReq
	if err := decodeJSON(w, r, &req); err != nil {
		return
	}
	u, tok, err := h.auth.Signup(r.Context(), req.Email, req.Password, req.Name, types.Role(req.Role))
	if err != nil {
		switch {
		case errors.Is(err, service.ErrEmailTaken):
			writeError(w, http.StatusConflict, "email_taken", "email already registered")
		case errors.Is(err, service.ErrValidation):
			writeError(w, http.StatusBadRequest, "bad_request", err.Error())
		default:
			writeError(w, http.StatusBadRequest, "bad_request", err.Error())
		}
		return
	}
	writeJSON(w, http.StatusOK, authResp{AccessToken: tok, TokenType: "bearer", User: u})
}

func (h *AuthHandler) Login(w http.ResponseWriter, r *http.Request) {
	var req loginReq
	if err := decodeJSON(w, r, &req); err != nil {
		return
	}
	u, tok, err := h.auth.Login(r.Context(), req.Email, req.Password)
	if err != nil {
		writeError(w, http.StatusUnauthorized, "invalid_credentials", "invalid email or password")
		return
	}
	writeJSON(w, http.StatusOK, authResp{AccessToken: tok, TokenType: "bearer", User: u})
}

// helpers

func decodeJSON(w http.ResponseWriter, r *http.Request, dst any) error {
	defer r.Body.Close()
	dec := json.NewDecoder(r.Body)
	dec.DisallowUnknownFields()
	if err := dec.Decode(dst); err != nil {
		writeError(w, http.StatusBadRequest, "invalid_json", err.Error())
		return err
	}
	return nil
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}

func writeError(w http.ResponseWriter, status int, code, message string) {
	writeJSON(w, status, map[string]any{
		"code":    code,
		"message": message,
	})
}
