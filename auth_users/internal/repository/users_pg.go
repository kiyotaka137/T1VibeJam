package repo

import (
	"context"
	"errors"

	types "auth_users/internal/models"

	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jackc/pgx/v5/pgxpool"
)

var ErrNotFound = errors.New("not found")
var ErrEmailTaken = errors.New("email taken")

type UsersRepo struct {
	db *pgxpool.Pool
}

func NewUsersRepo(db *pgxpool.Pool) *UsersRepo {
	return &UsersRepo{db: db}
}

func (r *UsersRepo) CreateUser(ctx context.Context, email, passwordHash, name string, role types.Role) (types.User, error) {
	const q = `
		insert into users (email, password_hash, name, role)
		values ($1,$2,$3,$4)
		returning id, email, name, role, created_at
	`
	var u types.User
	err := r.db.QueryRow(ctx, q, email, passwordHash, name, string(role)).
		Scan(&u.ID, &u.Email, &u.Name, &u.Role, &u.CreatedAt)
	if err != nil {
		// Упрощённо: ловим unique violation по тексту
		// В проде лучше проверять pgerrcode.
		if isUniqueViolation(err) {
			return types.User{}, ErrEmailTaken
		}
		return types.User{}, err
	}
	return u, nil
}

func (r *UsersRepo) GetByEmail(ctx context.Context, email string) (types.UserWithHash, error) {
	const q = `
		select id, email, name, role, created_at, password_hash
		from users
		where email = $1
	`
	var u types.UserWithHash
	var ph pgtype.Text

	err := r.db.QueryRow(ctx, q, email).
		Scan(&u.ID, &u.Email, &u.Name, &u.Role, &u.CreatedAt, &ph)
	if err != nil {
		return types.UserWithHash{}, ErrNotFound
	}

	if ph.Valid {
		u.PasswordHash = &ph.String
	} else {
		u.PasswordHash = nil
	}
	return u, nil
}

func (r *UsersRepo) PrecreateCandidate(ctx context.Context, email, name string) (types.User, error) {
	const q = `
		insert into users (email, password_hash, name, role)
		values ($1, null, $2, 'candidate')
		on conflict (email) do update
		set updated_at = users.updated_at
		returning id, email, name, role, created_at
	`
	var u types.User
	err := r.db.QueryRow(ctx, q, email, name).
		Scan(&u.ID, &u.Email, &u.Name, &u.Role, &u.CreatedAt)
	if err != nil {
		return types.User{}, err
	}
	return u, nil
}

func (r *UsersRepo) SetPasswordByEmail(ctx context.Context, email, passwordHash, name string) (types.User, error) {
	const q = `
		update users
		set password_hash = $2,
		    name = $3,
		    updated_at = now()
		where email = $1
		returning id, email, name, role, created_at
	`
	var u types.User
	err := r.db.QueryRow(ctx, q, email, passwordHash, name).
		Scan(&u.ID, &u.Email, &u.Name, &u.Role, &u.CreatedAt)
	if err != nil {
		return types.User{}, ErrNotFound
	}
	return u, nil
}

func (r *UsersRepo) GetByID(ctx context.Context, id string) (types.User, error) {
	const q = `
		select id, email, name, role, created_at
		from users
		where id = $1
	`
	var u types.User
	err := r.db.QueryRow(ctx, q, id).
		Scan(&u.ID, &u.Email, &u.Name, &u.Role, &u.CreatedAt)
	if err != nil {
		return types.User{}, ErrNotFound
	}
	return u, nil
}

// понять что шибка это ошибка уникальности
func isUniqueViolation(err error) bool {
	// pgx может возвращать разные типы; чтоб не тащить лишние пакеты — примитивная проверка
	msg := err.Error()
	return contains(msg, "duplicate key value") || contains(msg, "unique constraint")
}

// хелпер для подстроки
func contains(s, sub string) bool {
	if len(sub) == 0 {
		return true
	}
	for i := 0; i+len(sub) <= len(s); i++ {
		if s[i:i+len(sub)] == sub {
			return true
		}
	}
	return false
}
