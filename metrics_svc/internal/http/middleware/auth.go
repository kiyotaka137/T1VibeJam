package middleware

import (
	"context"
	"net/http"
	"strings"

	"github.com/golang-jwt/jwt/v5"
)

type ctxKey string

const (
	ctxIsInternal ctxKey = "is_internal"
	ctxUserID     ctxKey = "user_id"
	ctxRole       ctxKey = "role"
)

type Auth struct {
	InternalKey string
	JWTSecret   string
	JWTIssuer   string
}

func (a Auth) Wrap(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// internal key wins
		if key := r.Header.Get("X-Internal-API-Key"); key != "" && key == a.InternalKey {
			ctx := context.WithValue(r.Context(), ctxIsInternal, true)
			next.ServeHTTP(w, r.WithContext(ctx))
			return
		}

		// if JWT not configured -> only internal allowed
		if a.JWTSecret == "" {
			writeJSONError(w, http.StatusForbidden, "forbidden", "missing internal api key")
			return
		}

		authz := r.Header.Get("Authorization")
		if !strings.HasPrefix(authz, "Bearer ") {
			writeJSONError(w, http.StatusUnauthorized, "unauthorized", "missing bearer token")
			return
		}
		tokenStr := strings.TrimSpace(strings.TrimPrefix(authz, "Bearer "))

		tok, err := jwt.Parse(tokenStr, func(t *jwt.Token) (any, error) {
			// HS256
			return []byte(a.JWTSecret), nil
		}, jwt.WithValidMethods([]string{"HS256"}))
		if err != nil || tok == nil || !tok.Valid {
			writeJSONError(w, http.StatusUnauthorized, "unauthorized", "invalid token")
			return
		}

		claims, ok := tok.Claims.(jwt.MapClaims)
		if !ok {
			writeJSONError(w, http.StatusUnauthorized, "unauthorized", "invalid claims")
			return
		}

		// issuer check if provided
		if a.JWTIssuer != "" {
			if iss, _ := claims["iss"].(string); iss != a.JWTIssuer {
				writeJSONError(w, http.StatusUnauthorized, "unauthorized", "invalid issuer")
				return
			}
		}

		uid := firstString(claims["uid"], claims["sub"])
		role := firstString(claims["role"])

		ctx := r.Context()
		if uid != "" {
			ctx = context.WithValue(ctx, ctxUserID, uid)
		}
		if role != "" {
			ctx = context.WithValue(ctx, ctxRole, role)
		}
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

func IsInternal(r *http.Request) bool {
	v, _ := r.Context().Value(ctxIsInternal).(bool)
	return v
}
func UserID(r *http.Request) string {
	v, _ := r.Context().Value(ctxUserID).(string)
	return v
}
func Role(r *http.Request) string {
	v, _ := r.Context().Value(ctxRole).(string)
	return v
}

func firstString(values ...any) string {
	for _, v := range values {
		if s, ok := v.(string); ok && strings.TrimSpace(s) != "" {
			return strings.TrimSpace(s)
		}
	}
	return ""
}

func writeJSONError(w http.ResponseWriter, status int, code, message string) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	_, _ = w.Write([]byte(`{"code":"` + code + `","message":"` + message + `"}`))
}
