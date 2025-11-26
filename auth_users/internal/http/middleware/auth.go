package middleware

import (
	"context"
	"net/http"
	"strings"

	"auth_users/internal/security"
)

type ctxKey string

const (
	ctxUserID ctxKey = "user_id"
	ctxRole   ctxKey = "role"
	ctxEmail  ctxKey = "email"
)

// достает userid из контекста или пустую строку
func UserID(r *http.Request) string {
	if v := r.Context().Value(ctxUserID); v != nil {
		if s, ok := v.(string); ok {
			return s
		}
	}
	return ""
}

func Auth(jwt *security.JWT) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			h := r.Header.Get("Authorization")
			if h == "" || !strings.HasPrefix(h, "Bearer ") {
				http.Error(w, `{"code":"unauthorized","message":"missing bearer token"}`, http.StatusUnauthorized)
				return
			}
			token := strings.TrimSpace(strings.TrimPrefix(h, "Bearer "))
			claims, err := jwt.Parse(token)
			if err != nil {
				http.Error(w, `{"code":"unauthorized","message":"invalid token"}`, http.StatusUnauthorized)
				return
			}
			ctx := context.WithValue(r.Context(), ctxUserID, claims.UserID)
			ctx = context.WithValue(ctx, ctxRole, string(claims.Role))
			ctx = context.WithValue(ctx, ctxEmail, claims.Email)
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}
