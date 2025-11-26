package handlers

import (
	"context"
	"encoding/json"
	"net/http"
	"strings"
	"time"

	"github.com/google/uuid"

	"metrics_svc/internal/repo"
	"metrics_svc/internal/types"
)

type IngestHandler struct {
	Repo *repo.EventsRepo
}

func NewIngestHandler(r *repo.EventsRepo) *IngestHandler { return &IngestHandler{Repo: r} }

func (h *IngestHandler) IngestEvents(w http.ResponseWriter, r *http.Request) {
	var req types.IngestEventsRequest
	if err := decodeJSON(w, r, &req); err != nil {
		return
	}
	if len(req.Events) == 0 {
		writeError(w, http.StatusBadRequest, "bad_request", "events is required")
		return
	}

	ins := make([]repo.EventInsert, 0, len(req.Events))
	for i, e := range req.Events {
		inv, err := uuid.Parse(strings.TrimSpace(e.InterviewID))
		if err != nil {
			writeError(w, http.StatusBadRequest, "bad_request", "events["+itoa(i)+"].interview_id must be uuid")
			return
		}
		tt, err := time.Parse(time.RFC3339, strings.TrimSpace(e.TS))
		if err != nil {
			writeError(w, http.StatusBadRequest, "bad_request", "events["+itoa(i)+"].ts must be RFC3339")
			return
		}
		src := strings.TrimSpace(e.Source)
		typ := strings.TrimSpace(e.Type)
		if src == "" || typ == "" {
			writeError(w, http.StatusBadRequest, "bad_request", "events["+itoa(i)+"].source and type are required")
			return
		}

		var cand *uuid.UUID
		if e.CandidateUserID != nil && strings.TrimSpace(*e.CandidateUserID) != "" {
			cid, err := uuid.Parse(strings.TrimSpace(*e.CandidateUserID))
			if err != nil {
				writeError(w, http.StatusBadRequest, "bad_request", "events["+itoa(i)+"].candidate_user_id must be uuid")
				return
			}
			cand = &cid
		}

		var taskID *string
		if e.TaskID != nil {
			t := strings.TrimSpace(*e.TaskID)
			if t != "" {
				taskID = &t
			}
		}

		payload := e.Payload
		if len(payload) == 0 {
			payload = json.RawMessage(`{}`)
		} else {
			var tmp any
			if err := json.Unmarshal(payload, &tmp); err != nil {
				writeError(w, http.StatusBadRequest, "bad_request", "events["+itoa(i)+"].payload must be valid json")
				return
			}
		}

		ins = append(ins, repo.EventInsert{
			InterviewID:     inv,
			CandidateUserID: cand,
			TaskID:          taskID,
			Source:          src,
			Type:            typ,
			TS:              tt.UTC(),
			Payload:         payload,
		})
	}

	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	n, err := h.Repo.InsertEvents(ctx, ins)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "internal_error", err.Error())
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"inserted": n})
}

func itoa(i int) string {
	if i == 0 {
		return "0"
	}
	sign := ""
	if i < 0 {
		sign = "-"
		i = -i
	}
	var b [32]byte
	pos := len(b)
	for i > 0 {
		pos--
		b[pos] = byte('0' + i%10)
		i /= 10
	}
	return sign + string(b[pos:])
}
