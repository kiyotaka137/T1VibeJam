package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"interviews_svc/internal/clients"
	"interviews_svc/internal/config"
	apphttp "interviews_svc/internal/http"
	"interviews_svc/internal/http/handlers"
	"interviews_svc/internal/repo"
	"interviews_svc/internal/security"

	"github.com/jackc/pgx/v5/pgxpool"
)

func main() {
	config.SetGetenv(os.Getenv)

	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("config: %v", err)
	}

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	db, err := pgxpool.New(ctx, cfg.DatabaseURL)
	if err != nil {
		log.Fatalf("db: %v", err)
	}
	defer db.Close()

	pingCtx, cancel := context.WithTimeout(ctx, 3*time.Second)
	defer cancel()
	if err := db.Ping(pingCtx); err != nil {
		log.Fatalf("db ping: %v", err)
	}

	j := security.NewJWT(cfg.JWTSecret, cfg.JWTIssuer)

	authClient := clients.NewAuthClient(cfg.AuthBaseURL, cfg.AuthInternalAPIKey)

	interviewsRepo := repo.NewInterviewsRepo(db)
	invitesRepo := repo.NewInvitesRepo(db)

	hrH := handlers.NewHRInterviewsHandler(authClient, interviewsRepo, invitesRepo, cfg.InviteBaseURL, config.InviteTTL(cfg.InviteTTLMins))
	invH := handlers.NewInvitesHandler(interviewsRepo, invitesRepo)
	intTasksH := handlers.NewInternalTasksHandler(interviewsRepo)

	router := apphttp.NewRouter(apphttp.Deps{
		JWT:                  j,
		RequestMaxMB:         cfg.RequestMaxMB,
		InternalAPIKey:       cfg.InternalAPIKey,
		HRInterviewsHandler:  hrH,
		InvitesHandler:       invH,
		InternalTasksHandler: intTasksH,
	})

	srv := &http.Server{
		Addr:              cfg.HTTPAddr,
		Handler:           router,
		ReadHeaderTimeout: 5 * time.Second,
	}

	go func() {
		log.Printf("interviews-svc listening on %s", cfg.HTTPAddr)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("listen: %v", err)
		}
	}()

	<-ctx.Done()
	shutdownCtx, cancel2 := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel2()
	_ = srv.Shutdown(shutdownCtx)
	log.Println("shutdown")
}
