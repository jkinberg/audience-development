# Signal-Based Content Pipeline

A daily content pipeline for Substack writers. Scans your "neighborhood" of Substack publications, scores posts against a personal Signal Profile, and emails you a digest of the few posts most worth reading and resharing.

Built around a simple thesis: **growing an audience on Substack is less about volume and more about consistently engaging with the right ~50 publications in your topic area.** This pipeline does the surfacing so you can focus on the engagement.

## What it does

Every morning the pipeline:

1. **Fetches** new posts from ~40–50 Substack publications you've curated (your "neighborhood")
2. **Scores** each post (1–10) against your Signal Profile — five theme clusters that define what's relevant to you
3. **Enriches** the highest-scoring posts with full content extraction, pull-quotes, and suggested reshare angles
4. **Delivers** a markdown digest by email — typically 3–7 posts worth your attention

It also **closes the loop**: when you reshare a post on Substack Notes, it logs the match against the digest that surfaced it.

## Architecture

```
Substack Archive API ──► Fetch ──► Score (Gemini Flash) ──► Enrich (Gemini Pro / Claude Sonnet) ──► Digest ──► Email
                                                                                                       │
                                                                                                       └──► Substack Notes ──► Feedback Log
```

- **Two-stage scoring** keeps cost down: cheap metadata-only scoring on every post, expensive full-content enrichment only on the few that score highly.
- **No Substack login required.** Uses public Substack APIs (`/api/v1/archive`, `/api/v1/posts/{slug}`) and the [`substack_api`](https://pypi.org/project/substack-api/) library for discovery and subscription metadata.
- **Resumable runs**: intermediate state is written to `data/runs/YYYY-MM-DD/` so a partial run can be inspected or replayed.

## Stack

- **Language:** Python 3.14
- **Stage 1 scoring:** Gemini 3.1 Flash Lite (`gemini-3.1-flash-lite-preview`)
- **Stage 2 enrichment:** Gemini 3.1 Pro (`gemini-3.1-pro-preview`), Claude Sonnet as fallback
- **Email delivery:** Gmail SMTP with App Password
- **Deployment:** Local cron, GitHub Actions, or Google Cloud Run Jobs (deployment notes below)

## Setup

```bash
git clone https://github.com/<you>/audience-development.git
cd audience-development

python3.14 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Fill in API keys, Gmail credentials, your Substack handle
```

### Configure your Signal Profile

Edit `config/signal_profile.json` to define what content is relevant to you. The default has five theme clusters — replace them with your own:

```json
{
  "theme_clusters": [
    {
      "name": "Your Theme",
      "weight": "HIGH",
      "description": "What this theme covers and why it matters to you...",
      "example_signals": ["specific topic 1", "specific topic 2"]
    }
  ],
  "noise_filters": [...],
  "scoring": { "high_signal_threshold": 7, "digest_threshold": 6 }
}
```

The Signal Profile is the heart of the system. Spend time on it.

### Configure your watchlist (the "neighborhood")

Edit `config/watchlist.json` with the Substack publications you want monitored:

```json
{
  "publications": [
    {
      "url": "https://example.substack.com",
      "name": "Example Newsletter",
      "author": "Author Name",
      "tier": 1,
      "added": "2026-01-01",
      "source": "seed"
    }
  ]
}
```

You can also bootstrap the watchlist by running discovery, which crawls Substack's recommendation graph from your seed publications:

```bash
python scripts/run_discovery.py
```

Discovered candidates are written to `data/discovery_candidates.json` for review.

## Running the pipeline

```bash
./run.sh
# or
python scripts/run_pipeline.py
```

Output: `output/digests/YYYY-MM-DD.md` (also emailed if delivery is enabled).

## Deployment

The pipeline is designed to run as a daily cron job. Three deployment paths:

**Local cron** — simplest. Add a crontab entry that calls `./run.sh`.

**Google Cloud Run Jobs** — what the original deployment uses. State (digest history, reshare log) lives in a GCS bucket; Cloud Scheduler triggers the job daily. See `Dockerfile` and `cloud_run.py` for the entry point.

```bash
gcloud builds submit --tag gcr.io/<project>/signal-pipeline
gcloud run jobs create signal-pipeline --image gcr.io/<project>/signal-pipeline --region us-east1
```

**GitHub Actions** — works for some, but Substack appears to block traffic from GitHub Actions IP ranges. If your fetches return 403, switch to Cloud Run.

## Project structure

```
src/                — pipeline source (fetch, score, enrich, digest, deliver, feedback, discover)
config/             — runtime config (watchlist, signal_profile, pipeline)
scripts/            — entry points (run_pipeline.py, run_discovery.py)
planning/           — design docs and project notes
data/               — runtime state (digest history, reshare log) — gitignored
output/digests/     — generated digests — gitignored
```

## How the feedback loop works

The pipeline tracks which digest posts you go on to reshare on Substack Notes. After each run, it pulls your recent Notes via `/api/v1/notes`, matches any post-attachment reshares against the digest history, and logs them to `data/reshare_log.json`. Reshares of posts not from the digest are also logged — useful for surfacing publications you're engaging with that aren't yet in your watchlist.

The matched data is currently **observed but not yet used to influence scoring**. Closing that loop (using past reshare patterns to tune the Signal Profile) is on the roadmap.

## License

MIT — see [LICENSE](./LICENSE).

## Acknowledgements

Built with the [`substack_api`](https://github.com/NHagar/substack_api) library by NHagar for newsletter and recommendation graph access.
