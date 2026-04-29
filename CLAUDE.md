# Audience Development — Signal-Based Content Pipeline

## Project Overview
A content pipeline for Substack audience development. Monitors ~44 publications, scores posts against a Signal Profile (5 theme clusters), and surfaces reshare candidates via daily markdown digest.

## Architecture
- **Language:** Python 3.14
- **Substack data:** Raw Substack API for daily fetches (`/api/v1/archive`, `/api/v1/posts/{slug}`). Library (`substack_api`) used only for discovery (`get_recommendations()`, `User`, `Category`).
- **Scoring (Stage 1):** Gemini 3.1 Flash Lite (`gemini-3.1-flash-lite-preview`) — classifies posts from metadata only. Temp 0.
- **Enrichment (Stage 2):** Gemini 3.1 Pro (`gemini-3.1-pro-preview`) — full content fetch + quote extraction + angle suggestions. Only for posts scoring ≥ 7. Claude Sonnet (`claude-sonnet-4-20250514`) as fallback.
- **Config:** JSON files in `config/` — watchlist, signal_profile, pipeline settings
- **Output:** Markdown digest in `output/digests/`. Zapier webhook is a future feature.
- **Data models:** Pydantic models in `src/models.py` for typed data flow between stages
- **Runtime:** Local dev now, cloud cron (GitHub Actions or Railway) for production

## Key Technical Decisions
- Raw Substack archive API for daily batch pulls (library has bugs with cross-posts and redirects)
- Slug-based content fetch (`/api/v1/posts/{slug}`) for full text — more reliable than library's ID-based fetch
- Two-stage scoring: metadata-only Stage 1 (all posts via Gemini Flash), full content Stage 2 (posts ≥ 7 via Sonnet/Pro)
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

## Build Status (as of 2026-04-14)
- **Day 0:** Complete — API validated, findings documented
- **Day 1:** Complete — fetch, discover, watchlist expanded to 44 publications, Notes API validated (not available)
- **Day 2:** Complete — score.py (Gemini 3.1 Flash Lite) + enrich.py (Gemini 3.1 Pro) built and tested. 47 posts scored, 5 enriched, zero failures.
- **Day 3:** Complete — digest.py + run_pipeline.py built. First real digest: 17 posts scanned, 7 HIGH SIGNAL enriched, zero failures. ~3.5 min runtime.
- **Next:** Days 4-5 polish + deploy (error handling, cloud cron, dedup across runs)

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
