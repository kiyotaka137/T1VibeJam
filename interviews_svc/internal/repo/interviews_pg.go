package repo

import (
	"context"
	"encoding/json"
	"errors"
	"time"

	"interviews_svc/internal/types"

	"github.com/jackc/pgx/v5/pgxpool"
)

var (
	ErrNotFound   = errors.New("not found")
	ErrForbidden  = errors.New("forbidden")
	ErrInviteUsed = errors.New("invite already claimed by other user")
)

type InterviewsRepo struct {
	db *pgxpool.Pool
}

func NewInterviewsRepo(db *pgxpool.Pool) *InterviewsRepo { return &InterviewsRepo{db: db} }

func (r *InterviewsRepo) CreateInterview(ctx context.Context, hrID, candID string, topics []string, level string, ps, pe *time.Time) (types.Interview, error) {
	topicsB, _ := json.Marshal(topics)
	const q = `
		insert into interviews (hr_user_id, candidate_user_id, topics, level, planned_start, planned_end, status)
		values ($1, $2, $3::jsonb, $4, $5, $6, 'created')
		returning id, hr_user_id, candidate_user_id, topics, level, planned_start, planned_end, start_time, end_time, status, task_ids, created_at, updated_at
	`
	var it types.Interview
	var topicsRaw []byte
	err := r.db.QueryRow(ctx, q, hrID, candID, topicsB, level, ps, pe).Scan(
		&it.ID, &it.HRUserID, &it.CandidateUserID, &topicsRaw, &it.Level,
		&it.PlannedStart, &it.PlannedEnd, &it.StartTime, &it.EndTime,
		&it.Status, &it.TaskIDs, &it.CreatedAt, &it.UpdatedAt,
	)
	if err != nil {
		return types.Interview{}, err
	}
	_ = json.Unmarshal(topicsRaw, &it.Topics)
	return it, nil
}

func (r *InterviewsRepo) ListByHR(ctx context.Context, hrID string) ([]types.Interview, error) {
	const q = `
		select id, hr_user_id, candidate_user_id, topics, level, planned_start, planned_end, start_time, end_time, status, task_ids, created_at, updated_at
		from interviews
		where hr_user_id = $1
		order by created_at desc
		limit 200
	`
	rows, err := r.db.Query(ctx, q, hrID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	out := make([]types.Interview, 0, 16)
	for rows.Next() {
		var it types.Interview
		var topicsRaw []byte
		if err := rows.Scan(
			&it.ID, &it.HRUserID, &it.CandidateUserID, &topicsRaw, &it.Level,
			&it.PlannedStart, &it.PlannedEnd, &it.StartTime, &it.EndTime,
			&it.Status, &it.TaskIDs, &it.CreatedAt, &it.UpdatedAt,
		); err != nil {
			return nil, err
		}
		_ = json.Unmarshal(topicsRaw, &it.Topics)
		out = append(out, it)
	}
	return out, nil
}

func (r *InterviewsRepo) GetByIDForHR(ctx context.Context, id, hrID string) (types.Interview, error) {
	const q = `
		select id, hr_user_id, candidate_user_id, topics, level, planned_start, planned_end, start_time, end_time, status, task_ids, created_at, updated_at
		from interviews
		where id = $1
	`
	var it types.Interview
	var topicsRaw []byte
	err := r.db.QueryRow(ctx, q, id).Scan(
		&it.ID, &it.HRUserID, &it.CandidateUserID, &topicsRaw, &it.Level,
		&it.PlannedStart, &it.PlannedEnd, &it.StartTime, &it.EndTime,
		&it.Status, &it.TaskIDs, &it.CreatedAt, &it.UpdatedAt,
	)
	if err != nil {
		return types.Interview{}, ErrNotFound
	}
	if it.HRUserID != hrID {
		return types.Interview{}, ErrForbidden
	}
	_ = json.Unmarshal(topicsRaw, &it.Topics)
	return it, nil
}

func (r *InterviewsRepo) AppendTaskID(ctx context.Context, interviewID, taskID string) ([]string, error) {
	const q = `
		update interviews
		set task_ids = case when $2 = any(task_ids) then task_ids else array_append(task_ids, $2) end,
		    updated_at = now()
		where id = $1
		returning task_ids
	`
	var taskIDs []string
	if err := r.db.QueryRow(ctx, q, interviewID, taskID).Scan(&taskIDs); err != nil {
		return nil, ErrNotFound
	}
	return taskIDs, nil
}
