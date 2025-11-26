package http

import (
	"net/http"

	"github.com/go-chi/chi/v5"

	"auth_users/internal/http/handlers"
	"auth_users/internal/http/middleware"
	"auth_users/internal/security"
)

type Deps struct {
	JWT                  *security.JWT
	AuthHandler          *handlers.AuthHandler
	UsersHandler         *handlers.UsersHandler
	RequestMaxMB         int64
	InternalAPIKey       string
	InternalUsersHandler *handlers.InternalUsersHandler
}

func NewRouter(d Deps) http.Handler {
	r := chi.NewRouter()

	// маленький guard от огромных body
	r.Use(maxBody(d.RequestMaxMB))

	r.Route("/v1", func(r chi.Router) {
		r.Route("/auth", func(r chi.Router) {
			r.Post("/signup", d.AuthHandler.Signup)
			r.Post("/login", d.AuthHandler.Login)
		})

		r.Route("/users", func(r chi.Router) {
			r.With(middleware.Auth(d.JWT)).Get("/me", d.UsersHandler.Me)
		})
		r.Route("/internal", func(r chi.Router) {
			r.Use(middleware.InternalKey(d.InternalAPIKey))
			r.Post("/users/precreate", d.InternalUsersHandler.PrecreateCandidate)
		})

	})

	return r
}

func maxBody(maxMB int64) func(http.Handler) http.Handler {
	limit := maxMB * 1024 * 1024
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			r.Body = http.MaxBytesReader(w, r.Body, limit)
			next.ServeHTTP(w, r)
		})
	}
}
