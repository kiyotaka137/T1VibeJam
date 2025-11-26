package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"

	appconfig "auth_users/internal/config"
	apphttp "auth_users/internal/http"
	"auth_users/internal/http/handlers"
	repo "auth_users/internal/repository"
	"auth_users/internal/security"
	"auth_users/internal/service"
)

func main() {
	cfg, err := appconfig.Load()
	if err != nil {
		log.Fatalf("config: %v", err)
	}

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt)
	defer stop()

	db, err := pgxpool.New(ctx, cfg.DatabaseURL)
	if err != nil {
		log.Fatalf("db: %v", err)
	}
	defer db.Close()

	if err := db.Ping(ctx); err != nil {
		log.Fatalf("db ping: %v", err)
	}

	j := security.NewJWT(cfg.JWTSecret, cfg.JWTIssuer, cfg.JWTTTL)

	usersRepo := repo.NewUsersRepo(db)
	authSvc := service.NewAuthService(usersRepo, j, cfg.PasswordMin)

	authH := handlers.NewAuthHandler(authSvc)
	usersH := handlers.NewUsersHandler(authSvc)
	internalUsersH := handlers.NewInternalUsersHandler(authSvc)
	router := apphttp.NewRouter(apphttp.Deps{
		JWT:                  j,
		AuthHandler:          authH,
		UsersHandler:         usersH,
		InternalUsersHandler: internalUsersH,
		InternalAPIKey:       cfg.InternalAPIKey,
		RequestMaxMB:         cfg.RequestMaxMB,
	})

	srv := &http.Server{
		Addr:              cfg.HTTPAddr,
		Handler:           router,
		ReadHeaderTimeout: 5 * time.Second,
	}

	go func() {
		log.Printf("listening on %s", cfg.HTTPAddr)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("http: %v", err)
		}
	}()

	<-ctx.Done()
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	_ = srv.Shutdown(shutdownCtx)
	log.Println("shutdown complete")
}
