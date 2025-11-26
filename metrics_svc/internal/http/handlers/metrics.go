package handlers

import (
	"context"
	"net/http"
	"strings"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/google/uuid"

	"metrics_svc/internal/http/middleware"
	"metrics_svc/internal/repo"
	"metrics_svc/internal/service"
)

type MetricsHandler struct {
	Repo *repo.EventsRepo
}

func NewMetricsHandler(r *repo.EventsRepo) *MetricsHandler { return &MetricsHandler{Repo: r} }

func (h *MetricsHandler) Overview(w http.ResponseWriter, r *http.Request) {
	inv, cand, ok := parseIDs(w, r)
	if !ok {
		return
	}

	evs, ok := h.loadEvents(w, r, inv, cand)
	if !ok {
		return
	}

	agg := service.Aggregate(inv, cand, evs)
	writeJSON(w, http.StatusOK, agg.Overview())
}

func (h *MetricsHandler) Tasks(w http.ResponseWriter, r *http.Request) {
	inv, cand, ok := parseIDs(w, r)
	if !ok {
		return
	}

	evs, ok := h.loadEvents(w, r, inv, cand)
	if !ok {
		return
	}

	agg := service.Aggregate(inv, cand, evs)
	writeJSON(w, http.StatusOK, agg.TasksList())
}

func (h *MetricsHandler) TaskDetails(w http.ResponseWriter, r *http.Request) {
	inv, cand, ok := parseIDs(w, r)
	if !ok {
		return
	}

	taskID := strings.TrimSpace(chi.URLParam(r, "task_id"))
	if taskID == "" {
		writeError(w, http.StatusBadRequest, "bad_request", "task_id is required")
		return
	}

	evs, ok := h.loadEvents(w, r, inv, cand)
	if !ok {
		return
	}

	agg := service.Aggregate(inv, cand, evs)
	details, found := agg.TaskDetails(taskID)
	if !found {
		writeError(w, http.StatusNotFound, "not_found", "task not found")
		return
	}
	writeJSON(w, http.StatusOK, details)
}

func (h *MetricsHandler) Violations(w http.ResponseWriter, r *http.Request) {
	inv, cand, ok := parseIDs(w, r)
	if !ok {
		return
	}

	evs, ok := h.loadEvents(w, r, inv, cand)
	if !ok {
		return
	}

	agg := service.Aggregate(inv, cand, evs)
	writeJSON(w, http.StatusOK, agg.Violations())
}

func (h *MetricsHandler) loadEvents(w http.ResponseWriter, r *http.Request, inv uuid.UUID, cand *uuid.UUID) ([]repo.EventRow, bool) {
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	evs, err := h.Repo.ListByInterview(ctx, inv, cand)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "internal_error", err.Error())
		return nil, false
	}
	return evs, true
}

// Логика выбора candidate_user_id:
// - если internal key: можно читать всё, или фильтровать query ?candidate_user_id=...
// - если JWT candidate: фильтруем по uid из токена (чтобы кандидат видел только своё)
func parseIDs(w http.ResponseWriter, r *http.Request) (uuid.UUID, *uuid.UUID, bool) {
	invStr := strings.TrimSpace(chi.URLParam(r, "interview_id"))
	inv, err := uuid.Parse(invStr)
	if err != nil {
		writeError(w, http.StatusBadRequest, "bad_request", "interview_id must be uuid")
		return uuid.UUID{}, nil, false
	}

	// internal: optional filter by query
	if middleware.IsInternal(r) {
		if q := strings.TrimSpace(r.URL.Query().Get("candidate_user_id")); q != "" {
			cid, err := uuid.Parse(q)
			if err != nil {
				writeError(w, http.StatusBadRequest, "bad_request", "candidate_user_id must be uuid")
				return uuid.UUID{}, nil, false
			}
			return inv, &cid, true
		}
		return inv, nil, true
	}

	role := middleware.Role(r)
	uid := middleware.UserID(r)

	// candidate: force candidate filter
	if role == "candidate" {
		if uid == "" {
			writeError(w, http.StatusUnauthorized, "unauthorized", "missing user id in token")
			return uuid.UUID{}, nil, false
		}
		cid, err := uuid.Parse(uid)
		if err != nil {
			writeError(w, http.StatusUnauthorized, "unauthorized", "invalid user id in token")
			return uuid.UUID{}, nil, false
		}
		return inv, &cid, true
	}

	// hr/admin: разрешаем смотреть, но можно (опционально) фильтровать query
	if q := strings.TrimSpace(r.URL.Query().Get("candidate_user_id")); q != "" {
		cid, err := uuid.Parse(q)
		if err != nil {
			writeError(w, http.StatusBadRequest, "bad_request", "candidate_user_id must be uuid")
			return uuid.UUID{}, nil, false
		}
		return inv, &cid, true
	}
	return inv, nil, true
}
