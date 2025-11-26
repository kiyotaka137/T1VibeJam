package middleware

import (
	"net/http"
)

func InternalKey(expected string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			got := r.Header.Get("X-Internal-API-Key")
			if got == "" || got != expected {
				http.Error(w, `{"code":"forbidden","message":"invalid internal api key"}`, http.StatusForbidden)
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}
