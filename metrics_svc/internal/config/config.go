package config

import (
	"errors"
	"strconv"
)

var getenv func(string) string

func SetGetenv(fn func(string) string) { getenv = fn }

type Config struct {
	Port         string
	DatabaseURL  string
	InternalKey  string
	RequestMaxMB int64

	JWTSecret string
	JWTIssuer string
}

func Load() (Config, error) {
	if getenv == nil {
		return Config{}, errors.New("getenv not set (call config.SetGetenv)")
	}
	cfg := Config{
		Port:         env("PORT", "8080"),
		DatabaseURL:  env("DATABASE_URL", ""),
		InternalKey:  env("INTERNAL_API_KEY", ""),
		RequestMaxMB: int64(envInt("REQUEST_MAX_MB", 2)),
		JWTSecret:    env("JWT_SECRET", ""),
		JWTIssuer:    env("JWT_ISSUER", ""),
	}
	if cfg.DatabaseURL == "" {
		return Config{}, errors.New("DATABASE_URL is required")
	}
	if cfg.InternalKey == "" {
		return Config{}, errors.New("INTERNAL_API_KEY is required")
	}
	// JWT optional: если пусто — read endpoints будут работать только по internal key
	return cfg, nil
}

func env(key, def string) string {
	v := getenv(key)
	if v == "" {
		return def
	}
	return v
}
func envInt(key string, def int) int {
	v := getenv(key)
	if v == "" {
		return def
	}
	n, err := strconv.Atoi(v)
	if err != nil {
		return def
	}
	return n
}
