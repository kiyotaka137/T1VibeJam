package clients

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"time"
)

type AuthClient struct {
	baseURL string
	apiKey  string
	httpc   *http.Client
}

func NewAuthClient(baseURL, apiKey string) *AuthClient {
	return &AuthClient{
		baseURL: baseURL,
		apiKey:  apiKey,
		httpc:   &http.Client{Timeout: 3 * time.Second},
	}
}

type PrecreateReq struct {
	Email string `json:"email"`
	Name  string `json:"name"`
}

type User struct {
	ID    string `json:"id"`
	Email string `json:"email"`
	Name  string `json:"name"`
	Role  string `json:"role"`
}

func (c *AuthClient) PrecreateCandidate(ctx context.Context, email, name string) (User, error) {
	body, _ := json.Marshal(PrecreateReq{Email: email, Name: name})

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.baseURL+"/v1/internal/users/precreate", bytes.NewReader(body))
	if err != nil {
		return User{}, err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-Internal-API-Key", c.apiKey)

	resp, err := c.httpc.Do(req)
	if err != nil {
		return User{}, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return User{}, errors.New("auth precreate failed with status " + resp.Status)
	}
	var u User
	if err := json.NewDecoder(resp.Body).Decode(&u); err != nil {
		return User{}, err
	}
	if u.ID == "" {
		return User{}, errors.New("auth precreate returned empty id")
	}
	return u, nil
}
