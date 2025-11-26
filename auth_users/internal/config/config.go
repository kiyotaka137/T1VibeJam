package config

import (
	"errors"
	"os"
	"strconv"
	"strings"
	"time"
)

type Config struct {
	HTTPAddr       string
	DatabaseURL    string
	JWTSecret      string
	JWTIssuer      string
	JWTTTL         time.Duration
	PasswordMin    int
	RequestMaxMB   int64
	InternalAPIKey string
}

func Load() (Config, error) {
	cfg := Config{
		HTTPAddr:     env("HTTP_ADDR", ":8080"),
		DatabaseURL:  env("DATABASE_URL", ""),
		JWTSecret:    env("JWT_SECRET", ""),
		JWTIssuer:    env("JWT_ISSUER", "vibecode-auth"),
		PasswordMin:  envInt("PASSWORD_MIN", 6),
		RequestMaxMB: int64(envInt("REQUEST_MAX_MB", 1)),
	}
	cfg.InternalAPIKey = env("INTERNAL_API_KEY", "")
	if strings.TrimSpace(cfg.InternalAPIKey) == "" {
		return Config{}, errors.New("INTERNAL_API_KEY is required")
	}
	ttlStr := env("JWT_TTL_MINUTES", "1440") // 24h
	ttlMin, err := strconv.Atoi(ttlStr)
	if err != nil || ttlMin <= 0 {
		return Config{}, errors.New("invalid JWT_TTL_MINUTES")
	}
	cfg.JWTTTL = time.Duration(ttlMin) * time.Minute

	if strings.TrimSpace(cfg.DatabaseURL) == "" {
		return Config{}, errors.New("DATABASE_URL is required")
	}
	if strings.TrimSpace(cfg.JWTSecret) == "" {
		return Config{}, errors.New("JWT_SECRET is required")
	}
	return cfg, nil
}

func env(key, def string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return def
}

func envInt(key string, def int) int {
	v := os.Getenv(key)
	if v == "" {
		return def
	}
	n, err := strconv.Atoi(v)
	if err != nil {
		return def
	}
	return n
}
