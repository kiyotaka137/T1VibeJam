package handlers

import (
	"crypto/rand"
	"encoding/base64"
	"errors"
	"net/http"
	"strings"
	"time"

	"github.com/go-chi/chi/v5"

	"interviews_svc/internal/clients"
	"interviews_svc/internal/http/middleware"
	"interviews_svc/internal/repo"
	"interviews_svc/internal/types"
)

type HRInterviewsHandler struct {
	authClient       *clients.AuthClient
	interviews       *repo.InterviewsRepo
	invites          *repo.InvitesRepo
	inviteBaseURL    string
	defaultInviteTTL time.Duration
}

func NewHRInterviewsHandler(ac *clients.AuthClient, ir *repo.InterviewsRepo, vr *repo.InvitesRepo, inviteBaseURL string, defaultTTL time.Duration) *HRInterviewsHandler {
	return &HRInterviewsHandler{
		authClient: ac, interviews: ir, invites: vr,
		inviteBaseURL: inviteBaseURL, defaultInviteTTL: defaultTTL,
	}
}

type createInterviewReq struct {
	Topics       []string   `json:"topics"`
	Level        string     `json:"level"`
	PlannedStart *time.Time `json:"planned_start,omitempty"`
	PlannedEnd   *time.Time `json:"planned_end,omitempty"`
	Candidate    struct {
		Email string `json:"email"`
		Name  string `json:"name"`
	} `json:"candidate"`
	InviteExpiresMinutes *int `json:"invite_expires_minutes,omitempty"`
}

type createInterviewResp struct {
	Interview types.Interview `json:"interview"`
	Invite    struct {
		Token     string    `json:"token"`
		ExpiresAt time.Time `json:"expires_at"`
	} `json:"invite"`
	InviteURL string `json:"invite_url"`
}

func (h *HRInterviewsHandler) Create(w http.ResponseWriter, r *http.Request) {
	var req createInterviewReq
	if err := decodeJSON(w, r, &req); err != nil {
		return
	}

	hrID := middleware.UserID(r)
	if hrID == "" {
		writeError(w, http.StatusUnauthorized, "unauthorized", "missing user")
		return
	}

	req.Level = strings.TrimSpace(req.Level)
	req.Candidate.Email = strings.TrimSpace(req.Candidate.Email)
	req.Candidate.Name = strings.TrimSpace(req.Candidate.Name)

	if len(req.Topics) == 0 {
		writeError(w, http.StatusBadRequest, "bad_request", "topics is required")
		return
	}
	if req.Level == "" {
		writeError(w, http.StatusBadRequest, "bad_request", "level is required")
		return
	}
	if req.Candidate.Email == "" || req.Candidate.Name == "" {
		writeError(w, http.StatusBadRequest, "bad_request", "candidate.email and candidate.name are required")
		return
	}
	if req.PlannedStart != nil && req.PlannedEnd != nil && req.PlannedEnd.Before(*req.PlannedStart) {
		writeError(w, http.StatusBadRequest, "bad_request", "planned_end must be >= planned_start")
		return
	}

	// precreate candidate in auth
	u, err := h.authClient.PrecreateCandidate(r.Context(), req.Candidate.Email, req.Candidate.Name)
	if err != nil {
		writeError(w, http.StatusBadGateway, "auth_error", err.Error())
		return
	}
	if u.Role != string(types.RoleCandidate) {
		writeError(w, http.StatusConflict, "email_taken", "email belongs to non-candidate user")
		return
	}

	it, err := h.interviews.CreateInterview(r.Context(), hrID, u.ID, req.Topics, req.Level, req.PlannedStart, req.PlannedEnd)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "internal_error", err.Error())
		return
	}

	ttl := h.defaultInviteTTL
	if req.InviteExpiresMinutes != nil && *req.InviteExpiresMinutes > 0 {
		ttl = time.Duration(*req.InviteExpiresMinutes) * time.Minute
	}

	token := genToken()
	expiresAt := time.Now().UTC().Add(ttl)
	_ = h.invites.RevokeActiveForInterview(r.Context(), it.ID)
	inv, err := h.invites.CreateInvite(r.Context(), it.ID, token, expiresAt)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "internal_error", err.Error())
		return
	}

	var resp createInterviewResp
	resp.Interview = it
	resp.Invite.Token = inv.Token
	resp.Invite.ExpiresAt = inv.ExpiresAt
	resp.InviteURL = h.inviteBaseURL + "/" + inv.Token

	writeJSON(w, http.StatusOK, resp)
}

func (h *HRInterviewsHandler) List(w http.ResponseWriter, r *http.Request) {
	hrID := middleware.UserID(r)
	items, err := h.interviews.ListByHR(r.Context(), hrID)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "internal_error", err.Error())
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"items": items})
}

func (h *HRInterviewsHandler) Get(w http.ResponseWriter, r *http.Request) {
	hrID := middleware.UserID(r)
	id := strings.TrimSpace(chi.URLParam(r, "id"))
	if id == "" {
		writeError(w, http.StatusBadRequest, "bad_request", "missing id")
		return
	}

	it, err := h.interviews.GetByIDForHR(r.Context(), id, hrID)
	if err != nil {
		if errors.Is(err, repo.ErrForbidden) {
			writeError(w, http.StatusForbidden, "forbidden", "not your interview")
			return
		}
		writeError(w, http.StatusNotFound, "not_found", "interview not found")
		return
	}
	writeJSON(w, http.StatusOK, it)
}

func (h *HRInterviewsHandler) RegenerateInvite(w http.ResponseWriter, r *http.Request) {
	hrID := middleware.UserID(r)
	id := strings.TrimSpace(chi.URLParam(r, "id"))
	if id == "" {
		writeError(w, http.StatusBadRequest, "bad_request", "missing id")
		return
	}
	// check ownership
	_, err := h.interviews.GetByIDForHR(r.Context(), id, hrID)
	if err != nil {
		writeError(w, http.StatusNotFound, "not_found", "interview not found")
		return
	}

	_ = h.invites.RevokeActiveForInterview(r.Context(), id)
	token := genToken()
	expiresAt := time.Now().UTC().Add(h.defaultInviteTTL)
	inv, err := h.invites.CreateInvite(r.Context(), id, token, expiresAt)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "internal_error", err.Error())
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"token":      inv.Token,
		"expires_at": inv.ExpiresAt,
		"invite_url": h.inviteBaseURL + "/" + inv.Token,
	})
}

func genToken() string {
	b := make([]byte, 32)
	_, _ = rand.Read(b)
	return base64.RawURLEncoding.EncodeToString(b)
}
