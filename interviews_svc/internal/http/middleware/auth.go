package middleware

import (
	"context"
	"net/http"
	"strings"

	"interviews_svc/internal/security"
	"interviews_svc/internal/types"
)

type ctxKey string

const (
	ctxUserID ctxKey = "user_id"
	ctxRole   ctxKey = "role"
	ctxEmail  ctxKey = "email"
)

func UserID(r *http.Request) string {
	v, _ := r.Context().Value(ctxUserID).(string)
	return v
}

func Role(r *http.Request) types.Role {
	v, _ := r.Context().Value(ctxRole).(types.Role)
	return v
}

func Auth(jwtp *security.JWT) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			h := r.Header.Get("Authorization")
			if h == "" || !strings.HasPrefix(h, "Bearer ") {
				writeJSONError(w, http.StatusUnauthorized, "unauthorized", "missing bearer token")
				return
			}
			tok := strings.TrimSpace(strings.TrimPrefix(h, "Bearer "))
			claims, err := jwtp.Parse(tok)
			if err != nil {
				writeJSONError(w, http.StatusUnauthorized, "unauthorized", "invalid token")
				return
			}
			ctx := context.WithValue(r.Context(), ctxUserID, claims.UserID)
			ctx = context.WithValue(ctx, ctxRole, claims.Role)
			ctx = context.WithValue(ctx, ctxEmail, claims.Email)
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}
