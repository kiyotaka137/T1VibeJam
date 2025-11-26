package http

import (
	"net/http"

	"github.com/go-chi/chi/v5"

	"metrics_svc/internal/http/handlers"
	"metrics_svc/internal/http/middleware"
)

type Deps struct {
	RequestMaxMB int64

	Auth middleware.Auth

	Health  *handlers.HealthHandler
	Ingest  *handlers.IngestHandler
	Metrics *handlers.MetricsHandler
}

func NewRouter(d Deps) http.Handler {
	r := chi.NewRouter()
	r.Use(maxBody(d.RequestMaxMB))

	r.Get("/health", d.Health.Health)

	// internal ingest only by key
	r.Route("/internal", func(r chi.Router) {
		r.Use(middleware.Auth{InternalKey: d.Auth.InternalKey}.Wrap) // только internal
		r.Post("/events", d.Ingest.IngestEvents)
	})

	// read endpoints: internal key OR JWT (если настроен JWT_SECRET)
	r.Route("/v1", func(r chi.Router) {
		r.Use(d.Auth.Wrap)

		r.Route("/interviews/{interview_id}/metrics", func(r chi.Router) {
			r.Get("/overview", d.Metrics.Overview)
			r.Get("/tasks", d.Metrics.Tasks)
			r.Get("/tasks/{task_id}", d.Metrics.TaskDetails)
			r.Get("/violations", d.Metrics.Violations)
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
