# Feature Spec: Email Delivery for Daily Digest

**Status:** Ready for build  
**Date:** April 15, 2026  
**Author:** Josh Kinberg  
**Build tool:** Claude Code  
**Estimated effort:** 2-3 hours  
**Depends on:** Working pipeline (Days 0-3 — complete)

---

## Problem

The pipeline generates a markdown digest file at `output/digests/YYYY-MM-DD.md`. Right now the only way to read it is to open the file locally or view it in Cowork. There's no way to receive the digest on my phone, and there's no push delivery — I have to remember to go look for it.

For the resharing workflow to be sustainable, the digest needs to arrive in a place I already check, with clickable links I can act on immediately from any device.

---

## Solution

Add an email delivery step to the pipeline. After the markdown digest is written, convert it to clean HTML and send it via SendGrid's free tier to my email address. The email should be functional and scannable — not a designed newsletter template, just well-formatted HTML that renders the existing markdown structure with clickable links.

---

## Requirements

### Must have

1. **New module: `src/deliver.py`** — converts markdown digest to HTML and sends via SendGrid API.
2. **Markdown-to-HTML conversion** — use `markdown2` or `mistune` to convert the existing markdown output. The digest structure (headers, blockquotes, bullet points, links) should translate cleanly.
3. **Minimal responsive wrapper** — basic HTML/CSS that renders well on both desktop and mobile email clients. No images, no columns, no heavy styling. Clean typography, readable on a phone screen.
4. **SendGrid integration** — use SendGrid's Python SDK (`sendgrid`) or their Web API v3 directly. Free tier supports 100 emails/day.
5. **Pipeline integration** — call `deliver.py` at the end of `run_pipeline.py`, after `write_digest()` and `update_digest_history()`. Email delivery is non-blocking — if it fails, the digest file is still written and the run is still successful.
6. **Configuration in `config/pipeline.json`** — add a `delivery` section:
   ```json
   {
     "delivery": {
       "enabled": true,
       "method": "sendgrid",
       "to_email": "jkinberg@gmail.com",
       "from_email": "digest@yourdomain.com",
       "subject_template": "Signal Pipeline — {date} — {high_signal_count} high signal"
     }
   }
   ```
7. **Environment variable:** `SENDGRID_API_KEY` in `.env`.
8. **Graceful failure** — if SendGrid is unavailable, API key is missing, or the send fails, log a warning and continue. Never crash the pipeline over a delivery failure.

### Should have

9. **Subject line includes post count** — e.g., "Signal Pipeline — 2026-04-15 — 5 high signal" so I can see at a glance whether it's worth opening immediately.
10. **Plain-text fallback** — include the raw markdown as the plain-text body for email clients that don't render HTML. SendGrid supports sending both.
11. **"Empty digest" handling** — if no posts scored above threshold, either skip sending entirely or send a short "nothing today" email. Configurable via `skip_empty` boolean in config.

### Won't have (for now)

- HTML email design/templates beyond minimal responsive CSS
- Zapier webhook integration (already stubbed in `digest.py` — separate feature)
- Email tracking (opens, clicks)
- Multiple recipients
- Cloud deployment / cron scheduling (separate spec)

---

## Integration Points

### Where it hooks into the pipeline

In `scripts/run_pipeline.py`, after the existing digest write and history update:

```python
# --- STAGE 5: DELIVER ---
logger.info("--- DELIVER ---")
from src.deliver import send_digest_email

delivery_config = config.get("delivery", {})
if delivery_config.get("enabled", False):
    send_digest_email(
        markdown=md,
        entries=entries,
        stats=stats,
        config=delivery_config,
        date=today,
    )
```

### What it receives

- `md` — the rendered markdown string (same one written to the digest file)
- `entries` — list of `DigestEntry` objects (for subject line metadata)
- `stats` — pipeline stats dict (for subject line and footer)
- `config` — the `delivery` section from `pipeline.json`
- `date` — the run date string

### Existing patterns to follow

- Error handling: matches `send_to_zapier()` in `digest.py` — try/except, log warning on failure, return bool.
- Logging: use `logging.getLogger("pipeline.deliver")`, consistent with other modules.
- Config loading: `delivery` block lives in `config/pipeline.json` alongside existing `fetch`, `scoring`, `output` sections.

---

## HTML Conversion Notes

The markdown digest uses these elements that need to render well in email:

- `# H1` heading (digest title)
- `## H2` headings (post titles as links, section headers)
- `> blockquote` (pull quotes from enriched posts)
- `- bullet lists` (pipeline stats, reshare angles)
- `*italic*` (theme clusters)
- `[link text](url)` — these are the most important element. Every post title links to the Substack article URL. These must be clickable and prominent.
- `---` horizontal rules (section dividers)

Email HTML rendering is notoriously inconsistent. Keep the CSS inline (not in `<style>` blocks) for maximum compatibility. A simple approach:

- Body: white background, max-width ~600px centered, system font stack
- Links: styled visibly (color, maybe slightly larger for post titles)
- Blockquotes: left border, slight indent, lighter text
- Stats section: smaller text, less prominent

Libraries to consider: `markdown2` (simple, handles standard markdown well) or `mistune` (faster, more control over rendering). Either works.

---

## SendGrid Setup

1. Create free SendGrid account at sendgrid.com
2. Create an API key with "Mail Send" permission only
3. Verify a sender identity (single sender verification is fine — just verify jkinberg@gmail.com or use a custom domain if available)
4. Add `SENDGRID_API_KEY` to `.env`
5. Add `sendgrid` to `requirements.txt`

Note on sender address: SendGrid requires the `from_email` to be a verified sender. Simplest option is to verify your Gmail address and send from/to the same address. Alternatively, if you have a custom domain, verify that.

---

## Testing

1. **Unit test the markdown-to-HTML conversion** — feed it the April 14 digest markdown and verify links are preserved, blockquotes render, structure is intact.
2. **Send a real test email** — run the pipeline (or just the delivery step standalone) and verify it arrives in Gmail, renders correctly on desktop and mobile, and all links are clickable.
3. **Test failure modes** — missing API key, invalid key, SendGrid down. Verify the pipeline completes without crashing.
4. **Test empty digest** — verify behavior when no posts scored above threshold.

---

## Dependencies to Add

```
# requirements.txt additions
sendgrid>=6.0
markdown2>=2.4
```

---

## File Changes Summary

| File | Change |
|------|--------|
| `src/deliver.py` | **New** — markdown-to-HTML conversion + SendGrid email send |
| `scripts/run_pipeline.py` | Add Stage 5 delivery call after digest write |
| `config/pipeline.json` | Add `delivery` config section |
| `requirements.txt` | Add `sendgrid`, `markdown2` |
| `.env` | Add `SENDGRID_API_KEY` |
