package handlers

import (
	"net/http"
	"strings"
	"time"

	"interviews_svc/internal/http/middleware"
	"interviews_svc/internal/repo"
	"interviews_svc/internal/types"

	"github.com/go-chi/chi/v5"
)

type InvitesHandler struct {
	interviews *repo.InterviewsRepo
	invites    *repo.InvitesRepo
}

func NewInvitesHandler(ir *repo.InterviewsRepo, vr *repo.InvitesRepo) *InvitesHandler {
	return &InvitesHandler{interviews: ir, invites: vr}
}

func (h *InvitesHandler) Preview(w http.ResponseWriter, r *http.Request) {
	token := strings.TrimSpace(chi.URLParam(r, "token"))
	if token == "" {
		writeError(w, http.StatusBadRequest, "bad_request", "missing token")
		return
	}

	inv, err := h.invites.GetByToken(r.Context(), token)
	if err != nil {
		writeError(w, http.StatusNotFound, "not_found", "invite not found")
		return
	}

	// invite может быть отозван/истек
	if inv.RevokedAt != nil || time.Now().UTC().After(inv.ExpiresAt) {
		writeJSON(w, http.StatusOK, map[string]any{
			"valid":      false,
			"expires_at": inv.ExpiresAt,
		})
		return
	}

	// Берём интервью БЕЗ проверок владельца (публичное превью)
	it, err := h.interviews.GetByIDUnsafe(r.Context(), inv.InterviewID)
	if err != nil {
		writeError(w, http.StatusNotFound, "not_found", "interview not found")
		return
	}

	writeJSON(w, http.StatusOK, map[string]any{
		"valid":      true,
		"expires_at": inv.ExpiresAt,
		"interview_preview": map[string]any{
			"topics":        it.Topics,
			"level":         it.Level,
			"planned_start": it.PlannedStart,
			"planned_end":   it.PlannedEnd,
			"status":        it.Status,
		},
	})
}

func (h *InvitesHandler) Claim(w http.ResponseWriter, r *http.Request) {
	token := strings.TrimSpace(chi.URLParam(r, "token"))
	if token == "" {
		writeError(w, http.StatusBadRequest, "bad_request", "missing token")
		return
	}

	if middleware.Role(r) != types.RoleCandidate {
		writeError(w, http.StatusForbidden, "forbidden", "candidate role required")
		return
	}
	userID := middleware.UserID(r)

	inv, err := h.invites.GetByToken(r.Context(), token)
	if err != nil {
		writeError(w, http.StatusNotFound, "not_found", "invite not found")
		return
	}
	if inv.RevokedAt != nil || time.Now().UTC().After(inv.ExpiresAt) {
		writeError(w, http.StatusGone, "invite_expired", "invite expired or revoked")
		return
	}

	it, err := h.interviews.GetByIDUnsafe(r.Context(), inv.InterviewID)
	if err != nil {
		writeError(w, http.StatusNotFound, "not_found", "interview not found")
		return
	}

	// защита: claim может сделать только тот кандидат, которому назначено интервью
	if it.CandidateUserID != userID {
		writeError(w, http.StatusForbidden, "forbidden", "this invite is not for you")
		return
	}

	claimed, err := h.invites.Claim(r.Context(), token, userID)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "internal_error", err.Error())
		return
	}

	// если уже был claimed кем-то другим — конфликт
	if claimed.ClaimedByUserID != nil && *claimed.ClaimedByUserID != userID {
		writeError(w, http.StatusConflict, "invite_claimed", "invite already claimed")
		return
	}

	writeJSON(w, http.StatusOK, map[string]any{
		"interview_id": it.ID,
		"status":       it.Status,
	})
}
