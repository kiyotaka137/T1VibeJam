package middleware

import (
	"net/http"

	"interviews_svc/internal/types"
)

func RequireRole(role types.Role) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if Role(r) != role {
				writeJSONError(w, http.StatusForbidden, "forbidden", "insufficient role")
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}
