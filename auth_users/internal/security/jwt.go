package security

import (
	"errors"
	"time"

	types "auth_users/internal/models"

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
	ttl    time.Duration
}

func NewJWT(secret, issuer string, ttl time.Duration) *JWT {
	return &JWT{secret: []byte(secret), issuer: issuer, ttl: ttl}
}

// формирует токен
func (j *JWT) Sign(userID, email string, role types.Role) (string, error) {
	now := time.Now().UTC()
	claims := Claims{
		UserID: userID,
		Role:   role,
		Email:  email,
		RegisteredClaims: jwt.RegisteredClaims{
			Issuer:    j.issuer,
			IssuedAt:  jwt.NewNumericDate(now),
			NotBefore: jwt.NewNumericDate(now.Add(-5 * time.Second)),
			ExpiresAt: jwt.NewNumericDate(now.Add(j.ttl)),
		},
	}
	t := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return t.SignedString(j.secret)
}

// проверить токен на подпись/срок/iss и распарсить
func (j *JWT) Parse(token string) (*Claims, error) {
	parsed, err := jwt.ParseWithClaims(token, &Claims{}, func(t *jwt.Token) (any, error) {
		if t.Method != jwt.SigningMethodHS256 {
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
	return claims, nil
}
