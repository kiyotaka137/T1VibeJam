package service

import (
	"encoding/json"
	"sort"
	"time"

	"github.com/google/uuid"

	"metrics_svc/internal/repo"
	"metrics_svc/internal/types"
)

const (
	evTaskAssigned  = "task_assigned"
	evAttempt       = "attempt"
	evTaskCompleted = "task_completed"
	evAntiCheat     = "anti_cheat_violation"
	evPasteBlocked  = "paste_blocked"
)

type attemptPayload struct {
	AttemptID   string `json:"attempt_id,omitempty"`
	Result      string `json:"result,omitempty"` // ok|wrong|partial|compile_error|runtime_error|tests_failed...
	CompileOK   *bool  `json:"compile_ok,omitempty"`
	TestsTotal  *int   `json:"tests_total,omitempty"`
	TestsPassed *int   `json:"tests_passed,omitempty"`
}

type completedPayload struct {
	Reason string `json:"reason,omitempty"` // solved|annulled|skipped|timeout
}

type antiCheatPayload struct {
	Rule        string `json:"rule,omitempty"` // cursor_outside_frame
	ThresholdMs *int64 `json:"threshold_ms,omitempty"`
	DurationMs  *int64 `json:"duration_ms,omitempty"`
}

type pastePayload struct {
	Length *int `json:"length,omitempty"`
}

type Agg struct {
	InterviewID uuid.UUID
	CandidateID *uuid.UUID

	LastEventAt *time.Time

	Tasks map[string]*taskAgg
}

type taskAgg struct {
	taskID string

	assignedAt  *time.Time
	completedAt *time.Time
	reason      *string

	attempts []types.AttemptPoint

	firstGreenAt *time.Time
	compileFails int

	maxTestsPassed   *int
	finalTestsPassed *int
	finalTestsTotal  *int

	antiCheatLast *types.AnnulmentReason
	pasteCount    int
	pasteLen      int
}

func Aggregate(interviewID uuid.UUID, candidateID *uuid.UUID, events []repo.EventRow) Agg {
	a := Agg{
		InterviewID: interviewID,
		CandidateID: candidateID,
		Tasks:       map[string]*taskAgg{},
	}

	getTask := func(taskID string) *taskAgg {
		if t, ok := a.Tasks[taskID]; ok {
			return t
		}
		t := &taskAgg{taskID: taskID}
		a.Tasks[taskID] = t
		return t
	}

	for _, e := range events {
		ts := e.TS.UTC()
		if a.LastEventAt == nil || ts.After(*a.LastEventAt) {
			tmp := ts
			a.LastEventAt = &tmp
		}

		if e.TaskID == nil || *e.TaskID == "" {
			continue
		}
		taskID := *e.TaskID
		t := getTask(taskID)

		switch e.Type {

		case evTaskAssigned:
			if t.assignedAt == nil || ts.Before(*t.assignedAt) {
				tmp := ts
				t.assignedAt = &tmp
			}

		case evTaskCompleted:
			var p completedPayload
			_ = json.Unmarshal(e.Payload, &p)
			if t.completedAt == nil || ts.After(*t.completedAt) {
				tmp := ts
				t.completedAt = &tmp
				if p.Reason != "" {
					r := p.Reason
					t.reason = &r
				}
			}

		case evAttempt:
			var ap attemptPayload
			_ = json.Unmarshal(e.Payload, &ap)

			// attempt list (for details)
			pt := types.AttemptPoint{
				TS:          ts,
				Result:      ap.Result,
				CompileOK:   ap.CompileOK,
				TestsTotal:  ap.TestsTotal,
				TestsPassed: ap.TestsPassed,
			}
			t.attempts = append(t.attempts, pt)

			// compile fail heuristic
			compileOK := true
			if ap.CompileOK != nil {
				compileOK = *ap.CompileOK
			} else {
				// если не прислали compile_ok, интерпретируем по Result
				if ap.Result == "compile_error" {
					compileOK = false
				}
			}
			if !compileOK || ap.Result == "compile_error" {
				t.compileFails++
			}

			// max / final tests
			if ap.TestsPassed != nil {
				v := *ap.TestsPassed
				if t.maxTestsPassed == nil || v > *t.maxTestsPassed {
					tmp := v
					t.maxTestsPassed = &tmp
				}
				tmp := v
				t.finalTestsPassed = &tmp
			}
			if ap.TestsTotal != nil {
				tmp := *ap.TestsTotal
				t.finalTestsTotal = &tmp
			}

			// first green
			if t.firstGreenAt == nil && ap.TestsTotal != nil && ap.TestsPassed != nil {
				if compileOK && *ap.TestsTotal > 0 && *ap.TestsPassed == *ap.TestsTotal {
					tmp := ts
					t.firstGreenAt = &tmp
				}
			}

		case evAntiCheat:
			var ac antiCheatPayload
			_ = json.Unmarshal(e.Payload, &ac)
			// фиксируем как "последнюю причину"
			reason := types.AnnulmentReason{
				Rule:        ac.Rule,
				ThresholdMs: ac.ThresholdMs,
				DurationMs:  ac.DurationMs,
				TS:          ts,
			}
			t.antiCheatLast = &reason

		case evPasteBlocked:
			t.pasteCount++
			var pp pastePayload
			_ = json.Unmarshal(e.Payload, &pp)
			if pp.Length != nil && *pp.Length > 0 {
				t.pasteLen += *pp.Length
			}
		}
	}

	// ensure attempts are sorted
	for _, t := range a.Tasks {
		sort.Slice(t.attempts, func(i, j int) bool { return t.attempts[i].TS.Before(t.attempts[j].TS) })
	}

	return a
}

func (a Agg) Overview() types.OverviewResponse {
	resp := types.OverviewResponse{
		InterviewID: a.InterviewID.String(),
		LastEventAt: a.LastEventAt,
	}
	if a.CandidateID != nil {
		tmp := a.CandidateID.String()
		resp.CandidateUserID = &tmp
	}

	assigned := map[string]bool{}
	completed := map[string]bool{}
	annulled := map[string]bool{}

	var firstTs *time.Time
	var lastTs *time.Time

	for _, t := range a.Tasks {
		if t.assignedAt != nil {
			assigned[t.taskID] = true
			if firstTs == nil || t.assignedAt.Before(*firstTs) {
				tmp := *t.assignedAt
				firstTs = &tmp
			}
		}
		if t.completedAt != nil {
			completed[t.taskID] = true
			if lastTs == nil || t.completedAt.After(*lastTs) {
				tmp := *t.completedAt
				lastTs = &tmp
			}
		}
		resp.TotalAttempts += len(t.attempts)

		if t.reason != nil && *t.reason == "annulled" {
			annulled[t.taskID] = true
		}
	}

	resp.TasksAssigned = len(assigned)
	resp.TasksCompleted = len(completed)
	resp.TasksAnnulled = len(annulled)

	if firstTs != nil && lastTs != nil && lastTs.After(*firstTs) {
		ms := lastTs.Sub(*firstTs).Milliseconds()
		resp.TotalTimeMs = &ms
	}

	return resp
}

func (a Agg) TasksList() types.TasksListResponse {
	// stable sort: by assigned_at then task_id
	type pair struct {
		id string
		t  *taskAgg
	}
	var ps []pair
	for id, t := range a.Tasks {
		ps = append(ps, pair{id: id, t: t})
	}
	sort.Slice(ps, func(i, j int) bool {
		ai := ps[i].t.assignedAt
		aj := ps[j].t.assignedAt
		if ai != nil && aj != nil {
			if ai.Equal(*aj) {
				return ps[i].id < ps[j].id
			}
			return ai.Before(*aj)
		}
		if ai != nil && aj == nil {
			return true
		}
		if ai == nil && aj != nil {
			return false
		}
		return ps[i].id < ps[j].id
	})

	resp := types.TasksListResponse{LastEventAt: a.LastEventAt}
	for _, p := range ps {
		resp.Items = append(resp.Items, buildTaskCard(p.t))
	}
	return resp
}

func (a Agg) TaskDetails(taskID string) (types.TaskDetailsResponse, bool) {
	t, ok := a.Tasks[taskID]
	if !ok {
		return types.TaskDetailsResponse{}, false
	}
	card := buildTaskCard(t)

	anti := types.TaskAntiCheatDetail{
		Annulled:                card.Annulled,
		Reason:                  t.antiCheatLast,
		PasteBlockedCount:       t.pasteCount,
		PasteBlockedTotalLength: t.pasteLen,
	}

	return types.TaskDetailsResponse{
		Task:      card,
		Attempts:  t.attempts,
		AntiCheat: anti,
	}, true
}

func (a Agg) Violations() types.ViolationsResponse {
	var out []types.ViolationItem
	for _, t := range a.Tasks {
		if t.antiCheatLast != nil {
			out = append(out, types.ViolationItem{
				TaskID:      t.taskID,
				Type:        t.antiCheatLast.Rule,
				TS:          t.antiCheatLast.TS,
				DurationMs:  t.antiCheatLast.DurationMs,
				ThresholdMs: t.antiCheatLast.ThresholdMs,
			})
		}
		// paste events here are aggregated, но violations лучше показывать как facts:
		// для MVP показываем агрегат одной записью
		if t.pasteCount > 0 {
			l := t.pasteLen
			out = append(out, types.ViolationItem{
				TaskID: t.taskID,
				Type:   "paste_blocked",
				TS:     pickTS(t.completedAt, t.assignedAt),
				Length: &l,
			})
		}
	}

	// sort by TS asc
	sort.Slice(out, func(i, j int) bool { return out[i].TS.Before(out[j].TS) })
	return types.ViolationsResponse{Items: out}
}

func pickTS(prefer, fallback *time.Time) time.Time {
	if prefer != nil {
		return prefer.UTC()
	}
	if fallback != nil {
		return fallback.UTC()
	}
	return time.Now().UTC()
}

func buildTaskCard(t *taskAgg) types.TaskCard {
	var status string = "unknown"
	annulled := false

	if t.reason != nil {
		switch *t.reason {
		case "solved", "skipped", "timeout", "annulled":
			status = *t.reason
		default:
			status = "unknown"
		}
		if *t.reason == "annulled" {
			annulled = true
		}
	} else if t.assignedAt != nil {
		status = "in_progress"
	}

	// time on task
	var timeOnTask *int64
	if t.assignedAt != nil && t.completedAt != nil && t.completedAt.After(*t.assignedAt) {
		ms := t.completedAt.Sub(*t.assignedAt).Milliseconds()
		timeOnTask = &ms
	}

	// time to first green
	var ttfg *int64
	if t.assignedAt != nil && t.firstGreenAt != nil && t.firstGreenAt.After(*t.assignedAt) {
		ms := t.firstGreenAt.Sub(*t.assignedAt).Milliseconds()
		ttfg = &ms
	}

	// avg time between attempts
	var avgBetween *int64
	if len(t.attempts) >= 2 {
		var sum int64
		for i := 1; i < len(t.attempts); i++ {
			sum += t.attempts[i].TS.Sub(t.attempts[i-1].TS).Milliseconds()
		}
		avg := sum / int64(len(t.attempts)-1)
		avgBetween = &avg
	}

	return types.TaskCard{
		TaskID: t.taskID,
		Status: status,

		AssignedAt:   t.assignedAt,
		CompletedAt:  t.completedAt,
		TimeOnTaskMs: timeOnTask,

		AttemptsTotal:          len(t.attempts),
		AvgTimeBetweenAttempts: avgBetween,

		TimeToFirstGreenMs: ttfg,

		CompileFailures: t.compileFails,

		MaxTestsPassed:   t.maxTestsPassed,
		FinalTestsPassed: t.finalTestsPassed,
		TestsTotal:       t.finalTestsTotal,

		Annulled: annulled,
	}
}
