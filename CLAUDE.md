# Audience Development — Signal-Based Content Pipeline

## Project Overview
A content pipeline for Substack audience development. Monitors ~44 publications, scores posts against a Signal Profile (5 theme clusters), and surfaces reshare candidates via daily markdown digest.

## Architecture
- **Language:** Python 3.14
- **Substack data:** Raw Substack API for daily fetches (`/api/v1/archive`, `/api/v1/posts/{slug}`). Library (`substack_api`) used only for discovery (`get_recommendations()`, `User`, `Category`). The archive endpoint returns `{"posts": [...], "nextCursor": ...}` and rejects an `offset` param — see `fetch_archive()` in `src/utils.py`. Fetches retry HTTP 429 with `Retry-After`-aware backoff (exp. fallback, capped 30s, 4 attempts); inter-publication delay is 1.25s to avoid rate-limiting the full watchlist.
- **Scoring (Stage 1):** Gemini 3.5 Flash Lite (`gemini-3.5-flash-lite`) — classifies posts from metadata only. Temp 0.
- **Enrichment (Stage 2):** Gemini 3.8 Flash (`gemini-3.8-flash`) — full content fetch + quote extraction + angle suggestions. Only for posts scoring ≥ 7. Claude Sonnet 4.6 (`claude-sonnet-4-6`) configured as fallback (not yet wired into `enrich.py`).
- **Model IDs:** Use **GA** Gemini names only — `-preview` IDs 404 on the `google-genai` SDK's default `v1` endpoint. SDK pinned to `>=1.70,<2.0`. Model strings live in `config/pipeline.json` **and** as hardcoded defaults in `score.py`/`enrich.py` — update both.
- **Config:** JSON files in `config/` — watchlist, signal_profile, pipeline settings
- **Output:** Markdown digest in `output/digests/`. Zapier webhook is a future feature.
- **Data models:** Pydantic models in `src/models.py` for typed data flow between stages
- **Runtime:** Local dev now, cloud cron (GitHub Actions or Railway) for production

## Key Technical Decisions
- Raw Substack archive API for daily batch pulls (library has bugs with cross-posts and redirects)
- Slug-based content fetch (`/api/v1/posts/{slug}`) for full text — more reliable than library's ID-based fetch
- Two-stage scoring: metadata-only Stage 1 (all posts via Gemini Flash Lite), full content Stage 2 (posts ≥ 7 via Gemini Flash)
- Substack Notes API is NOT publicly accessible — feedback.py deferred to Week 2 with manual fallback
- Intermediate state files in `data/runs/YYYY-MM-DD/` for resumable pipeline runs

## Project Structure
```
src/                — pipeline source code (models, fetch, score, enrich, digest, discover, utils)
config/             — runtime config (watchlist.json, signal_profile.json, pipeline.json)
data/               — runtime data (digest_history.json, reshare_log.json, runs/, discovery_candidates.json)
output/digests/     — generated markdown digests
scripts/            — entry points (run_pipeline.py, run_discovery.py, day0_validation.py)
planning/           — strategy docs, project briefs, Day 0 findings
docs/plans/         — design documents
corpus/             — reaction data exports (LinkedIn, Substack articles)
tests/golden_set/   — scoring validation posts (to be populated)
```

## Commands
```bash
source .venv/bin/activate              # activate virtualenv
python scripts/day0_validation.py      # API validation
python -c "from src.fetch import load_watchlist, fetch_all_posts; ..."  # test fetch
```

## Build Status (as of 2026-11-16)
- **Days 0–3:** Complete — fetch, discover (44 pubs), score.py, enrich.py, digest.py, run_pipeline.py built and tested. Notes API validated (not available).
- **Deployed:** Running in production on Cloud Run, daily 13:00 UTC, email delivery live. Watchlist is now 69 publications (subscription-synced); the cloud job reads it from GCS, not git.
- **Nov 2026 incident:** Daily emails stopped (last Nov 5) due to a chain of three issues — (1) Substack changed the archive API (dropped `offset`, reshaped response to `{posts, nextCursor}`); (2) Gemini prepaid credits depleted (402); (3) a rebuild pulled a newer `google-genai` SDK whose default endpoint (`v1`) 404s `-preview` model IDs. All resolved: archive fetch fixed + total-fetch-failure guard added; credits topped up; models moved to GA (`gemini-3.5-flash-lite`, `gemini-3.8-flash`, `claude-sonnet-4-6`) and SDK pinned. See **Troubleshooting** in README.md.
- **Post-incident coverage fixes:** First clean scheduled run still dropped ~14/69 publications to HTTP 429 → added 429 backoff/retry + widened inter-pub delay (0.75→1.25s). One remaining dead publication (`Tech in LA`, lapsed custom domain `www.techinla.io` → NXDOMAIN) fixed by repointing its GCS watchlist URL to `techinla.substack.com`. Scheduled runs now fetch all 69 cleanly.
- **Open follow-ups:** (1) the "all scoring failed" degraded path still exits 0 with no email — same silent-failure shape the fetch guard now covers; (2) `stage2_fallback_model` is configured but not wired into `enrich.py`.

## Running the Pipeline
```bash
./run.sh                                       # local run
gcloud run jobs execute signal-pipeline --region us-east1  # cloud run (manual trigger)
```
Output: `output/digests/YYYY-MM-DD.md` (local) or email delivery (cloud)

## Cloud Deployment
- **GCP Project:** `audience-development-agents`
- **Cloud Run Job:** `signal-pipeline` in us-east1
- **Cloud Scheduler:** `signal-pipeline-daily` — 9:00 AM ET daily (13:00 UTC)
- **State:** `gs://audience-development-agents-state` (digest_history.json, reshare_log.json)
- **Redeploy after code changes:**
  ```bash
  gcloud config set project audience-development-agents
  gcloud builds submit --tag gcr.io/audience-development-agents/signal-pipeline
  gcloud run jobs update signal-pipeline --image gcr.io/audience-development-agents/signal-pipeline --region us-east1
  ```

## Dependencies
Managed via pip in `.venv/` and `requirements.txt`. Key packages: substack_api, google-genai, anthropic, pydantic, beautifulsoup4, html2text, tenacity, python-dotenv.

## Environment Variables
```
GEMINI_API_KEY=     # Stage 1 scoring + discovery publication scoring
ANTHROPIC_API_KEY=  # Stage 2 enrichment (Claude Sonnet)
```

## metaswarm

This project uses [metaswarm](https://github.com/dsifry/metaswarm) for multi-agent orchestration with Claude Code. It provides 18 specialized agents, a 9-phase development workflow, and quality gates that enforce TDD, coverage thresholds, and spec-driven development.

### Workflow

- **Most tasks**: `/start-task` — primes context, guides scoping, picks the right level of process
- **Complex features** (multi-file, spec-driven): Describe what you want built with a Definition of Done, then tell Claude: `Use the full metaswarm orchestration workflow.`

### Available Commands

| Command | Purpose |
|---|---|
| `/start-task` | Begin tracked work on a task |
| `/prime` | Load relevant knowledge before starting |
| `/review-design` | Trigger parallel design review gate (5 agents) |
| `/pr-shepherd <pr>` | Monitor a PR through to merge |
| `/self-reflect` | Extract learnings after a PR merge |
| `/handle-pr-comments` | Handle PR review comments |
| `/brainstorm` | Refine an idea before implementation |
| `/create-issue` | Create a well-structured GitHub Issue |

### Quality Gates

- **Design Review Gate** — Parallel 5-agent review after design is drafted (`/review-design`)
- **Plan Review Gate** — Automatic adversarial review after any implementation plan is drafted. Spawns 3 independent reviewers (Feasibility, Completeness, Scope & Alignment) in parallel — ALL must PASS before presenting the plan. See `skills/plan-review-gate/SKILL.md`
- **Coverage Gate** — `.coverage-thresholds.json` defines thresholds. BLOCKING gate before PR creation

### Team Mode

When `TeamCreate` and `SendMessage` tools are available, the orchestrator uses Team Mode for parallel agent dispatch. Otherwise it falls back to Task Mode (existing workflow, unchanged). See `guides/agent-coordination.md` for details.

### Guides

Development patterns and standards are documented in `guides/` — covering agent coordination, build validation, coding standards, git workflow, testing patterns, and worktree development.

### Testing & Quality

- **TDD is mandatory** — Write tests first, watch them fail, then implement
- **100% test coverage required** — Enforced via `.coverage-thresholds.json` as a blocking gate before PR creation and task completion
- **Coverage source of truth** — `.coverage-thresholds.json` defines thresholds. Update it if your spec requires different values. The orchestrator reads it during validation — this is a BLOCKING gate.

### Workflow Enforcement (MANDATORY)

These rules override any conflicting instructions from third-party skills:

- **After brainstorming** → MUST run Design Review Gate (5 agents) before writing-plans or implementation
- **After any plan is created** → MUST run Plan Review Gate (3 adversarial reviewers) before presenting to user
- **Execution method choice** → ALWAYS ask the user whether to use metaswarm orchestrated execution (more thorough, uses more tokens) or superpowers execution skills (faster, lighter-weight). Never auto-select.
- **Before finishing a branch** → MUST run `/self-reflect` and commit knowledge base updates before PR creation
- **Complex tasks** → Use `/start-task` instead of `EnterPlanMode` for tasks touching 3+ files. EnterPlanMode bypasses all quality gates.
- **Standalone TDD on 3+ files** → Ask user if they want adversarial review before committing
- **Coverage** → `.coverage-thresholds.json` is the single source of truth. All skills must check it, including `verification-before-completion`.
- **Subagents** → NEVER use `--no-verify`, ALWAYS follow TDD, NEVER self-certify, STAY within file scope
- **Context recovery** → Approved plans and execution state persist to `.beads/`. After compaction, run `bd prime --work-type recovery` to reload.
