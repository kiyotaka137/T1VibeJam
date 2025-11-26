package repo

import (
	"context"
	"encoding/json"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type EventRow struct {
	InterviewID     uuid.UUID
	CandidateUserID *uuid.UUID
	TaskID          *string
	Source          string
	Type            string
	TS              time.Time
	Payload         json.RawMessage
}

type EventInsert struct {
	InterviewID     uuid.UUID
	CandidateUserID *uuid.UUID
	TaskID          *string
	Source          string
	Type            string
	TS              time.Time
	Payload         json.RawMessage
}

type EventsRepo struct{ db *pgxpool.Pool }

func NewEventsRepo(db *pgxpool.Pool) *EventsRepo { return &EventsRepo{db: db} }

func (r *EventsRepo) InsertEvents(ctx context.Context, ins []EventInsert) (int, error) {
	if len(ins) == 0 {
		return 0, nil
	}

	b := &pgx.Batch{}
	sql := `insert into events (interview_id, candidate_user_id, task_id, source, type, ts, payload)
	        values ($1,$2,$3,$4,$5,$6,$7)`
	for _, e := range ins {
		payload := e.Payload
		if len(payload) == 0 {
			payload = json.RawMessage(`{}`)
		}
		b.Queue(sql, e.InterviewID, e.CandidateUserID, e.TaskID, e.Source, e.Type, e.TS, payload)
	}

	br := r.db.SendBatch(ctx, b)
	defer br.Close()

	n := 0
	for range ins {
		_, err := br.Exec()
		if err != nil {
			return n, err
		}
		n++
	}
	return n, nil
}

func (r *EventsRepo) ListByInterview(ctx context.Context, interviewID uuid.UUID, candidateID *uuid.UUID) ([]EventRow, error) {
	q := `select interview_id, candidate_user_id, task_id, source, type, ts, payload
	      from events where interview_id=$1`
	args := []any{interviewID}
	if candidateID != nil {
		q += ` and candidate_user_id=$2`
		args = append(args, *candidateID)
	}
	q += ` order by ts asc`

	rows, err := r.db.Query(ctx, q, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []EventRow
	for rows.Next() {
		var e EventRow
		if err := rows.Scan(&e.InterviewID, &e.CandidateUserID, &e.TaskID, &e.Source, &e.Type, &e.TS, &e.Payload); err != nil {
			return nil, err
		}
		out = append(out, e)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return out, nil
}
