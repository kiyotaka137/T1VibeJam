package repo

import (
	"context"
	"encoding/json"

	"interviews_svc/internal/types"
)

func (r *InterviewsRepo) GetByIDUnsafe(ctx context.Context, id string) (types.Interview, error) {
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
	_ = json.Unmarshal(topicsRaw, &it.Topics)
	return it, nil
}
