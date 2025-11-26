package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"metrics_svc/internal/config"
	"metrics_svc/internal/db"
	ihttp "metrics_svc/internal/http"
	"metrics_svc/internal/http/handlers"
	"metrics_svc/internal/http/middleware"
	"metrics_svc/internal/repo"
)

func main() {
	config.SetGetenv(os.Getenv)

	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("config error: %v", err)
	}

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	pool, err := db.Connect(ctx, cfg.DatabaseURL)
	if err != nil {
		log.Fatalf("db connect error: %v", err)
	}
	defer pool.Close()

	eventsRepo := repo.NewEventsRepo(pool)

	healthH := handlers.NewHealthHandler()
	ingestH := handlers.NewIngestHandler(eventsRepo)
	metricsH := handlers.NewMetricsHandler(eventsRepo)

	router := ihttp.NewRouter(ihttp.Deps{
		RequestMaxMB: cfg.RequestMaxMB,
		Auth: middleware.Auth{
			InternalKey: cfg.InternalKey,
			JWTSecret:   cfg.JWTSecret,
			JWTIssuer:   cfg.JWTIssuer,
		},
		Health:  healthH,
		Ingest:  ingestH,
		Metrics: metricsH,
	})

	srv := &http.Server{
		Addr:              ":" + cfg.Port,
		Handler:           router,
		ReadHeaderTimeout: 5 * time.Second,
	}

	go func() {
		log.Printf("interview-stats-svc listening on :%s", cfg.Port)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("http server error: %v", err)
		}
	}()

	<-ctx.Done()

	shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	_ = srv.Shutdown(shutdownCtx)
	log.Println("interview-stats-svc stopped")
}
