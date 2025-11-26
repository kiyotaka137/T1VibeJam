package security

import (
	"errors"

	"interviews_svc/internal/types"

	"github.com/golang-jwt/jwt/v5"
)

type Claims struct {
	UserID string     `json:"uid"`
	Role   types.Role `json:"role"`
	Email  string     `json:"email"`
	jwt.RegisteredClaims
}

type JWT struct {
	secret []byte
	issuer string
}

func NewJWT(secret, issuer string) *JWT {
	return &JWT{secret: []byte(secret), issuer: issuer}
}

func (j *JWT) Parse(token string) (*Claims, error) {
	parsed, err := jwt.ParseWithClaims(token, &Claims{}, func(t *jwt.Token) (any, error) {
		if t.Method.Alg() != jwt.SigningMethodHS256.Alg() {
			return nil, errors.New("unexpected signing method")
		}
		return j.secret, nil
	}, jwt.WithIssuer(j.issuer))
	if err != nil {
		return nil, err
	}
	claims, ok := parsed.Claims.(*Claims)
	if !ok || !parsed.Valid {
		return nil, errors.New("invalid token")
	}
	if !claims.Role.Valid() {
		return nil, errors.New("invalid role in token")
	}
	if claims.UserID == "" {
		return nil, errors.New("missing uid in token")
	}
	return claims, nil
}
