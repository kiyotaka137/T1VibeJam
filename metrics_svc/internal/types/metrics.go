package types

import "time"

// 1) /metrics/overview
type OverviewResponse struct {
	InterviewID     string     `json:"interview_id"`
	CandidateUserID *string    `json:"candidate_user_id,omitempty"`
	TasksAssigned   int        `json:"tasks_assigned"`
	TasksCompleted  int        `json:"tasks_completed"`
	TasksAnnulled   int        `json:"tasks_annulled"`
	TotalAttempts   int        `json:"total_attempts"`
	TotalTimeMs     *int64     `json:"total_time_ms,omitempty"`
	LastEventAt     *time.Time `json:"last_event_at,omitempty"`
}

// 2) /metrics/tasks
type TasksListResponse struct {
	Items       []TaskCard `json:"items"`
	LastEventAt *time.Time `json:"last_event_at,omitempty"`
}

type TaskCard struct {
	TaskID string `json:"task_id"`

	Status      string     `json:"status"` // solved|in_progress|annulled|skipped|timeout|unknown
	AssignedAt  *time.Time `json:"assigned_at,omitempty"`
	CompletedAt *time.Time `json:"completed_at,omitempty"`

	TimeOnTaskMs *int64 `json:"time_on_task_ms,omitempty"`

	AttemptsTotal          int    `json:"attempts_total"`
	AvgTimeBetweenAttempts *int64 `json:"avg_time_between_attempts_ms,omitempty"`

	TimeToFirstGreenMs *int64 `json:"time_to_first_green_ms,omitempty"`

	CompileFailures int `json:"compile_failures"`

	MaxTestsPassed   *int `json:"max_tests_passed,omitempty"`
	FinalTestsPassed *int `json:"final_tests_passed,omitempty"`
	TestsTotal       *int `json:"tests_total,omitempty"`

	Annulled bool `json:"annulled"`
}

// 3) /metrics/tasks/{task_id}
type TaskDetailsResponse struct {
	Task      TaskCard            `json:"task"`
	Attempts  []AttemptPoint      `json:"attempts"`
	AntiCheat TaskAntiCheatDetail `json:"anti_cheat"`
}

type AttemptPoint struct {
	TS          time.Time `json:"ts"`
	Result      string    `json:"result,omitempty"`
	CompileOK   *bool     `json:"compile_ok,omitempty"`
	TestsTotal  *int      `json:"tests_total,omitempty"`
	TestsPassed *int      `json:"tests_passed,omitempty"`
}

type TaskAntiCheatDetail struct {
	Annulled bool `json:"annulled"`

	Reason *AnnulmentReason `json:"reason,omitempty"`

	PasteBlockedCount       int `json:"paste_blocked_count"`
	PasteBlockedTotalLength int `json:"paste_blocked_total_length"`
}

type AnnulmentReason struct {
	Rule        string    `json:"rule"`
	ThresholdMs *int64    `json:"threshold_ms,omitempty"`
	DurationMs  *int64    `json:"duration_ms,omitempty"`
	TS          time.Time `json:"ts"`
}

// 4) /metrics/violations
type ViolationsResponse struct {
	Items []ViolationItem `json:"items"`
}

type ViolationItem struct {
	TaskID string `json:"task_id"`
	Type   string `json:"type"` // cursor_outside_frame | paste_blocked | other

	TS time.Time `json:"ts"`

	// cursor_outside_frame
	DurationMs  *int64 `json:"duration_ms,omitempty"`
	ThresholdMs *int64 `json:"threshold_ms,omitempty"`

	// paste
	Length *int `json:"length,omitempty"`
}
