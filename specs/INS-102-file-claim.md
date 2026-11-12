# INS-102: File a first notice of loss (FNOL) claim

**Type:** Story · **Epic:** Digital Claims · **Status:** Ready for Dev

## User story
As a policyholder, I want to file a claim online so that I know right away
whether it is approved and roughly what I will be paid.

## Claim rules
- The incident date must be within the policy coverage period (start date to end date, inclusive).
- `payout = min(claim amount − deductible, coverage limit)`, never below 0.
- If payout is 0 → status `denied_below_deductible`.
- Otherwise, amounts up to **$10,000** → `approved`; above $10,000 → `under_review`.

## Acceptance criteria
- **AC1** Given an active standard policy (deductible $500, limit $50,000), when the policyholder
  files a $3,000 claim for an incident today (`POST /claims`), then the response is `201` with
  `status = approved` and `payout = 2500.00`.
- **AC2** Given an active standard policy, when a $12,000 claim is filed, then
  `status = under_review` and `payout = 11500.00`.
- **AC3** Given an active standard policy, when a $400 claim is filed, then
  `status = denied_below_deductible` and `payout = 0`.
- **AC4** Given an active basic policy (deductible $1,000, limit $25,000), when a $40,000 claim is
  filed, then `status = under_review` and `payout = 25000.00` (capped at the limit).
- **AC5** Given a policy starting today, when a claim is filed for an incident yesterday, then the
  response is `422` with error code `INCIDENT_OUTSIDE_COVERAGE`.
- **AC6** Given a policy ID that does not exist, when a claim is filed, then the response is `404`
  with error code `POLICY_NOT_FOUND`.
- **AC7** Given a filed claim, when it is retrieved with `GET /claims/{id}`, then the same status
  and payout are returned; an unknown claim ID returns `404`.
- **AC8 (UI)** Given an active standard policy, when the policyholder opens
  `/ui/claims/new?policy_id=<id>`, enters amount 3000 and clicks **Submit claim**, then they see
  status **approved** and estimated payout **$2,500.00**.
