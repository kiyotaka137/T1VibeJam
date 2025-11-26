package service

import (
	"context"
	"errors"
	"fmt"
	"net/mail"
	"strings"

	types "auth_users/internal/models"
	repo "auth_users/internal/repository"
	"auth_users/internal/security"
)

var (
	ErrInvalidCredentials = errors.New("invalid credentials")
	ErrEmailTaken         = errors.New("email taken")
	ErrValidation         = errors.New("validation")
)

type AuthService struct {
	users       *repo.UsersRepo
	jwt         *security.JWT
	passwordMin int
}

func NewAuthService(users *repo.UsersRepo, jwt *security.JWT, passwordMin int) *AuthService {
	return &AuthService{users: users, jwt: jwt, passwordMin: passwordMin}
}

// регистрация+дозарегистрация
func (s *AuthService) Signup(ctx context.Context, email, password, name string, role types.Role) (types.User, string, error) {
	email = strings.TrimSpace(strings.ToLower(email))
	name = strings.TrimSpace(name)

	if _, err := mail.ParseAddress(email); err != nil {
		return types.User{}, "", fmt.Errorf("%w: invalid email", ErrValidation)
	}
	if len(password) < s.passwordMin {
		return types.User{}, "", fmt.Errorf("%w: password too short", ErrValidation)
	}
	if name == "" {
		return types.User{}, "", fmt.Errorf("%w: name is required", ErrValidation)
	}
	if !role.Valid() {
		return types.User{}, "", fmt.Errorf("%w: invalid role", ErrValidation)
	}

	// 1) пробуем найти пользователя
	existing, err := s.users.GetByEmail(ctx, email)
	if err == nil {
		// есть такой email
		if existing.Role != role {
			return types.User{}, "", ErrEmailTaken
		}
		// если пароль уже задан — считаем что email занят
		if existing.PasswordHash != nil {
			return types.User{}, "", ErrEmailTaken
		}

		// дозарегистрация: ставим пароль
		hash, err := security.HashPassword(password)
		if err != nil {
			return types.User{}, "", err
		}
		u, err := s.users.SetPasswordByEmail(ctx, email, hash, name)
		if err != nil {
			return types.User{}, "", err
		}
		tok, err := s.jwt.Sign(u.ID, u.Email, u.Role)
		if err != nil {
			return types.User{}, "", err
		}
		return u, tok, nil
	}

	// если не найден — создаём нового (обычный signup)
	if err != repo.ErrNotFound {
		return types.User{}, "", err
	}

	hash, err := security.HashPassword(password)
	if err != nil {
		return types.User{}, "", err
	}
	u, err := s.users.CreateUser(ctx, email, hash, name, role)
	if err != nil {
		if err == repo.ErrEmailTaken {
			return types.User{}, "", ErrEmailTaken
		}
		return types.User{}, "", err
	}
	tok, err := s.jwt.Sign(u.ID, u.Email, u.Role)
	if err != nil {
		return types.User{}, "", err
	}
	return u, tok, nil
}

// аутентификация
func (s *AuthService) Login(ctx context.Context, email, password string) (types.User, string, error) {
	email = strings.TrimSpace(strings.ToLower(email))
	if email == "" || password == "" {
		return types.User{}, "", ErrInvalidCredentials
	}

	u, err := s.users.GetByEmail(ctx, email)
	if err != nil || u.PasswordHash == nil {
		return types.User{}, "", ErrInvalidCredentials
	}
	if !security.VerifyPassword(*u.PasswordHash, password) {
		return types.User{}, "", ErrInvalidCredentials
	}

	tok, err := s.jwt.Sign(u.ID, u.Email, u.Role)
	if err != nil {
		return types.User{}, "", err
	}
	return u.User, tok, nil
}
func (s *AuthService) PrecreateCandidate(ctx context.Context, email, name string) (types.User, error) {
	email = strings.TrimSpace(strings.ToLower(email))
	name = strings.TrimSpace(name)

	if _, err := mail.ParseAddress(email); err != nil {
		return types.User{}, fmt.Errorf("%w: invalid email", ErrValidation)
	}
	if name == "" {
		return types.User{}, fmt.Errorf("%w: name is required", ErrValidation)
	}

	u, err := s.users.PrecreateCandidate(ctx, email, name)
	if err != nil {
		return types.User{}, err
	}
	// если email уже был, но роль не candidate — запретим
	if u.Role != types.RoleCandidate {
		return types.User{}, ErrEmailTaken
	}
	return u, nil
}

func (s *AuthService) Me(ctx context.Context, userID string) (types.User, error) {
	return s.users.GetByID(ctx, userID)
}
