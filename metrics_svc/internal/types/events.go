package types

import "encoding/json"

type IngestEventsRequest struct {
	Events []EventIn `json:"events"`
}

type EventIn struct {
	InterviewID     string  `json:"interview_id"`
	CandidateUserID *string `json:"candidate_user_id,omitempty"`
	TaskID          *string `json:"task_id,omitempty"`

	Source string `json:"source"` // session|task|frontend|runner (любой текст)
	Type   string `json:"type"`   // task_assigned|attempt|task_completed|anti_cheat_violation|paste_blocked
	TS     string `json:"ts"`     // RFC3339

	Payload json.RawMessage `json:"payload,omitempty"`
}
