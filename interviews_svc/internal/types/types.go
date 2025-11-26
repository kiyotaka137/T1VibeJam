package types

import "time"

type Role string

const (
	RoleHR        Role = "hr"
	RoleCandidate Role = "candidate"
)

func (r Role) Valid() bool { return r == RoleHR || r == RoleCandidate }

type InterviewStatus string

const (
	StatusCreated  InterviewStatus = "created"
	StatusActive   InterviewStatus = "active"
	StatusFinished InterviewStatus = "finished"
	StatusCanceled InterviewStatus = "canceled"
)

type Interview struct {
	ID              string          `json:"id"`
	HRUserID        string          `json:"hr_user_id"`
	CandidateUserID string          `json:"candidate_user_id"`
	Topics          []string        `json:"topics"`
	Level           string          `json:"level"`
	PlannedStart    *time.Time      `json:"planned_start,omitempty"`
	PlannedEnd      *time.Time      `json:"planned_end,omitempty"`
	StartTime       *time.Time      `json:"start_time,omitempty"`
	EndTime         *time.Time      `json:"end_time,omitempty"`
	Status          InterviewStatus `json:"status"`
	TaskIDs         []string        `json:"task_ids"`
	CreatedAt       time.Time       `json:"created_at"`
	UpdatedAt       time.Time       `json:"updated_at"`
}

type Invite struct {
	ID              string     `json:"id"`
	InterviewID     string     `json:"interview_id"`
	Token           string     `json:"token"`
	ExpiresAt       time.Time  `json:"expires_at"`
	CreatedAt       time.Time  `json:"created_at"`
	RevokedAt       *time.Time `json:"revoked_at,omitempty"`
	ClaimedAt       *time.Time `json:"claimed_at,omitempty"`
	ClaimedByUserID *string    `json:"claimed_by_user_id,omitempty"`
}
