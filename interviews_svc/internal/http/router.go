package http

import (
	"net/http"

	"interviews_svc/internal/http/handlers"
	"interviews_svc/internal/http/middleware"
	"interviews_svc/internal/security"
	"interviews_svc/internal/types"

	"github.com/go-chi/chi/v5"
)

type Deps struct {
	JWT            *security.JWT
	RequestMaxMB   int64
	InternalAPIKey string

	HRInterviewsHandler  *handlers.HRInterviewsHandler
	InvitesHandler       *handlers.InvitesHandler
	InternalTasksHandler *handlers.InternalTasksHandler
}

func NewRouter(d Deps) http.Handler {
	r := chi.NewRouter()
	r.Use(maxBody(d.RequestMaxMB))

	// Public
	r.Get("/v1/invites/{token}", d.InvitesHandler.Preview)

	// Candidate claim (JWT required)
	r.With(middleware.Auth(d.JWT)).Post("/v1/invites/{token}/claim", d.InvitesHandler.Claim)

	// HR routes
	r.Route("/v1/hr", func(r chi.Router) {
		r.Use(middleware.Auth(d.JWT))
		r.Use(middleware.RequireRole(types.RoleHR))

		r.Post("/interviews", d.HRInterviewsHandler.Create)
		r.Get("/interviews", d.HRInterviewsHandler.List)
		r.Get("/interviews/{id}", d.HRInterviewsHandler.Get)
		r.Post("/interviews/{id}/invites", d.HRInterviewsHandler.RegenerateInvite)
	})

	// Internal routes (key-protected)
	r.Route("/internal", func(r chi.Router) {
		r.Use(middleware.InternalKey(d.InternalAPIKey))
		r.Post("/interviews/{id}/task-ids:append", d.InternalTasksHandler.AppendTaskID)
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
