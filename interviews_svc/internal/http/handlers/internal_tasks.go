package handlers

import (
	"net/http"
	"strings"

	"interviews_svc/internal/repo"

	"github.com/go-chi/chi/v5"
)

type InternalTasksHandler struct {
	interviews *repo.InterviewsRepo
}

func NewInternalTasksHandler(ir *repo.InterviewsRepo) *InternalTasksHandler {
	return &InternalTasksHandler{interviews: ir}
}

type appendTaskReq struct {
	TaskID string `json:"task_id"`
}

func (h *InternalTasksHandler) AppendTaskID(w http.ResponseWriter, r *http.Request) {
	id := strings.TrimSpace(chi.URLParam(r, "id"))
	if id == "" {
		writeError(w, http.StatusBadRequest, "bad_request", "missing interview id")
		return
	}

	var req appendTaskReq
	if err := decodeJSON(w, r, &req); err != nil {
		return
	}
	req.TaskID = strings.TrimSpace(req.TaskID)
	if req.TaskID == "" {
		writeError(w, http.StatusBadRequest, "bad_request", "task_id is required")
		return
	}

	taskIDs, err := h.interviews.AppendTaskID(r.Context(), id, req.TaskID)
	if err != nil {
		writeError(w, http.StatusNotFound, "not_found", "interview not found")
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"task_ids": taskIDs})
}
