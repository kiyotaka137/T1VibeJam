package repo

import (
	"context"
	"time"

	"interviews_svc/internal/types"

	"github.com/jackc/pgx/v5/pgxpool"
)

type InvitesRepo struct{ db *pgxpool.Pool }

func NewInvitesRepo(db *pgxpool.Pool) *InvitesRepo { return &InvitesRepo{db: db} }

func (r *InvitesRepo) RevokeActiveForInterview(ctx context.Context, interviewID string) error {
	const q = `
		update interview_invites
		set revoked_at = now()
		where interview_id = $1 and revoked_at is null
	`
	_, err := r.db.Exec(ctx, q, interviewID)
	return err
}

func (r *InvitesRepo) CreateInvite(ctx context.Context, interviewID, token string, expiresAt time.Time) (types.Invite, error) {
	const q = `
		insert into interview_invites (interview_id, token, expires_at)
		values ($1, $2, $3)
		returning id, interview_id, token, expires_at, created_at, revoked_at, claimed_at, claimed_by_user_id
	`
	var inv types.Invite
	err := r.db.QueryRow(ctx, q, interviewID, token, expiresAt).Scan(
		&inv.ID, &inv.InterviewID, &inv.Token, &inv.ExpiresAt, &inv.CreatedAt,
		&inv.RevokedAt, &inv.ClaimedAt, &inv.ClaimedByUserID,
	)
	return inv, err
}

func (r *InvitesRepo) GetByToken(ctx context.Context, token string) (types.Invite, error) {
	const q = `
		select id, interview_id, token, expires_at, created_at, revoked_at, claimed_at, claimed_by_user_id
		from interview_invites
		where token = $1
	`
	var inv types.Invite
	err := r.db.QueryRow(ctx, q, token).Scan(
		&inv.ID, &inv.InterviewID, &inv.Token, &inv.ExpiresAt, &inv.CreatedAt,
		&inv.RevokedAt, &inv.ClaimedAt, &inv.ClaimedByUserID,
	)
	if err != nil {
		return types.Invite{}, ErrNotFound
	}
	return inv, nil
}

func (r *InvitesRepo) Claim(ctx context.Context, token, userID string) (types.Invite, error) {
	const q = `
		update interview_invites
		set claimed_at = coalesce(claimed_at, now()),
		    claimed_by_user_id = coalesce(claimed_by_user_id, $2)
		where token = $1
		returning id, interview_id, token, expires_at, created_at, revoked_at, claimed_at, claimed_by_user_id
	`
	var inv types.Invite
	err := r.db.QueryRow(ctx, q, token, userID).Scan(
		&inv.ID, &inv.InterviewID, &inv.Token, &inv.ExpiresAt, &inv.CreatedAt,
		&inv.RevokedAt, &inv.ClaimedAt, &inv.ClaimedByUserID,
	)
	if err != nil {
		return types.Invite{}, ErrNotFound
	}
	return inv, nil
}
