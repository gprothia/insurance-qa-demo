# Demo run-of-show (~20 min)

## Before the meeting
- [ ] `scripts/setup_gcp.sh` run in an Argolis project; GitHub repo variables set.
- [ ] Stories INS-101 and INS-102 exist as GitHub issues (`./scripts/create_issues.sh`, after `gh auth login`).
- [ ] GitHub MCP server added in Antigravity and signed in to `gprothia`, with read access to
      issues in `gprothia/insurance-qa-demo`.
- [ ] Repo cloned locally, `make install` done, `make run` running.
- [ ] One **finished** PR run from `demo/young-driver-bug` (red ❌ comment) and one green run,
      ready to show if the live pipeline is slow. Warm up the cluster by running one PR earlier
      that day (the first Autopilot pod scheduling is the slowest).

## 1. The problem (2 min)
Specs live in the tracker (GitHub Issues here; Jira works the same way via Atlassian's MCP
server), tests get written weeks later (if ever), and everyone shares one broken
staging environment. Defects in rating and claims logic reach production.

## 2. Spec → tests in Antigravity (7 min)
Open the repo in AGY and give the agent this prompt:

> Using the GitHub MCP server, read the issue titled **INS-102** in gprothia/insurance-qa-demo.
> Following GEMINI.md, write API tests and UI tests that cover every acceptance criterion. Run
> them against the app on localhost:8000, fix any test problems, and finish with a table mapping
> each AC to its test.

*Optional finish:* "Comment on the INS-102 issue with the AC → test table." This closes the loop
in the tracker.

**Jetski variant (internal rehearsals):** Jetski uses the GitHub CLI login, so no MCP setup is needed:

> Read GitHub issue INS-102 in gprothia/insurance-qa-demo (`gh issue view 2`). Following
> GEMINI.md, write API and UI tests for every acceptance criterion, run them against
> localhost:8000, fix any test problems, and finish with a table mapping each AC to its test.

Rehearsal result: 8 tests (7 API + 1 UI) generated, all passing on the first run, with the same
AC coverage as `golden/ins-102-tests`. See branch `rehearsal/ins-102-tests`. The tests run in
under 10 seconds locally.

What to point out while it works: it reads the acceptance criteria, checks `/openapi.json`,
writes `tests/api/test_INS_102_file_claim.py` and `tests/ui/test_INS_102_file_claim_ui.py`,
runs them and fixes them itself. The Playwright test drives a real browser.

*Markdown variant (1 min):* "Same thing from `specs/INS-102-file-claim.md`", for teams that
keep specs in the repo.

If generation runs long: `git checkout golden/ins-102-tests -- tests/` and carry on.

Commit and open a PR: `git checkout -b ins-102-tests && git add tests && git commit -m "INS-102 acceptance tests" && git push -u origin HEAD`, then open the PR on GitHub.

## 3. Every PR gets its own sandbox (6 min)
1. Open a PR from `demo/young-driver-bug` (someone "refactored" the young-driver rule).
2. Show the Actions run: images build, `kubectl get ns -l purpose=pr-sandbox` shows `pr-<N>`,
   `kubectl -n pr-<N> get pods` shows the app and the test Job.
3. The PR comment shows **❌ INS-101 AC2 failed** (API and UI): a 22-year-old is now
   underpriced by $650 a year. Tie it to business impact.

## 4. Fix and re-run (2 min)
Revert the change (or ask the AGY agent: "the PR check failed on INS-101 AC2; fix the code, not
the test"), push, and the check goes green. The namespace is gone afterwards: no idle staging cost.

## 5. Wrap-up (3 min)
- Traceability: every acceptance criterion in the tracker (GitHub Issues or Jira) maps to a test
  and a result on every PR.
- Cost: you pay for Autopilot pods only for the minutes a PR runs.
- Pilot: one client service + 5–10 real stories, two weeks, measuring time from story to test,
  escaped defects and PR feedback time.

## Claims to avoid
- "Zero human review": engineers review generated tests before they become merge gates.
- "A new cluster per PR in seconds": it's a namespace per PR on a shared Autopilot cluster.
- "CI regenerates all tests on every PR": CI runs the committed, reviewed tests. Gemini can
  *suggest* tests for changed specs as an optional extra step.
