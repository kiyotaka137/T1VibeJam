package config

import (
	"errors"
	"strconv"
	"strings"
	"time"
)

type Config struct {
	HTTPAddr     string
	DatabaseURL  string
	RequestMaxMB int64

	JWTSecret string
	JWTIssuer string

	InternalAPIKey string

	AuthBaseURL        string
	AuthInternalAPIKey string

	InviteBaseURL string
	InviteTTLMins int
}

func Load() (Config, error) {
	var c Config

	c.HTTPAddr = env("HTTP_ADDR", ":8080")
	c.DatabaseURL = env("DATABASE_URL", "")
	c.RequestMaxMB = int64(envInt("REQUEST_MAX_MB", 1))

	c.JWTSecret = env("JWT_SECRET", "")
	c.JWTIssuer = env("JWT_ISSUER", "vibecode-auth")

	c.InternalAPIKey = env("INTERNAL_API_KEY", "")

	c.AuthBaseURL = strings.TrimRight(env("AUTH_BASE_URL", ""), "/")
	c.AuthInternalAPIKey = env("AUTH_INTERNAL_API_KEY", "")

	c.InviteBaseURL = strings.TrimRight(env("INVITE_BASE_URL", ""), "/")
	c.InviteTTLMins = envInt("INVITE_TTL_MINUTES", 4320)

	if strings.TrimSpace(c.DatabaseURL) == "" {
		return Config{}, errors.New("DATABASE_URL is required")
	}
	if strings.TrimSpace(c.JWTSecret) == "" {
		return Config{}, errors.New("JWT_SECRET is required")
	}
	if strings.TrimSpace(c.JWTIssuer) == "" {
		return Config{}, errors.New("JWT_ISSUER is required")
	}
	if strings.TrimSpace(c.InternalAPIKey) == "" {
		return Config{}, errors.New("INTERNAL_API_KEY is required")
	}
	if strings.TrimSpace(c.AuthBaseURL) == "" {
		return Config{}, errors.New("AUTH_BASE_URL is required")
	}
	if strings.TrimSpace(c.AuthInternalAPIKey) == "" {
		return Config{}, errors.New("AUTH_INTERNAL_API_KEY is required")
	}
	if strings.TrimSpace(c.InviteBaseURL) == "" {
		return Config{}, errors.New("INVITE_BASE_URL is required")
	}
	if c.InviteTTLMins <= 0 {
		return Config{}, errors.New("INVITE_TTL_MINUTES must be > 0")
	}

	return c, nil
}

func env(key, def string) string {
	v := strings.TrimSpace(getenv(key))
	if v == "" {
		return def
	}
	return v
}

func envInt(key string, def int) int {
	v := strings.TrimSpace(getenv(key))
	if v == "" {
		return def
	}
	n, err := strconv.Atoi(v)
	if err != nil {
		return def
	}
	return n
}

// replaced in main via os.Getenv to keep this file minimal-testable
var getenv = func(k string) string { return "" }

func SetGetenv(fn func(string) string) { getenv = fn }

func InviteTTL(d int) time.Duration { return time.Duration(d) * time.Minute }
