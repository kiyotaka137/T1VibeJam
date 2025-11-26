package security

import "golang.org/x/crypto/bcrypt"

// создает хеш пароля
func HashPassword(password string) (string, error) {
	b, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return "", err
	}
	return string(b), nil
}

// проверить соответствие пароля хешу
func VerifyPassword(hash, password string) bool {
	return bcrypt.CompareHashAndPassword([]byte(hash), []byte(password)) == nil
}
