package types

import "time"

type Role string

const (
	RoleHR        Role = "hr"
	RoleCandidate Role = "candidate"
)

func (r Role) Valid() bool {
	return r == RoleHR || r == RoleCandidate
}

type User struct {
	ID        string    `json:"id"`
	Email     string    `json:"email"`
	Name      string    `json:"name"`
	Role      Role      `json:"role"`
	CreatedAt time.Time `json:"created_at"`
}

// внутренняя структура для логина
type UserWithHash struct {
	User
	PasswordHash *string
}
