"""Main pipeline entry point: fetch → score → enrich → digest."""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from src.fetch import load_watchlist, load_digest_history, fetch_all_posts, save_fetched_posts
from src.score import score_all_posts, load_signal_profile, load_pipeline_config, save_scored_posts
from src.enrich import enrich_top_posts
from src.digest import build_digest_entries, render_markdown, write_digest, update_digest_history, send_to_zapier
from src.deliver import send_digest_email
from src.feedback import check_for_reshares
from src.subscriptions import sync_subscriptions_to_watchlist
from src.utils import setup_logging


def main():
    setup_logging()
    logger = logging.getLogger("pipeline")

    today = datetime.now().strftime("%Y-%m-%d")
    run_dir = Path(f"data/runs/{today}")
    run_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"=== Pipeline run: {today} ===")

    # Load config
    config = load_pipeline_config()
    signal_profile = load_signal_profile()

    # --- STAGE 0: SUBSCRIPTION SYNC ---
    # Pull the user's current Substack subs and append any new pubs to the watchlist
    # before fetching, so the run picks them up immediately.
    sub_handle = config.get("user", {}).get("substack_handle") or os.getenv("SUBSTACK_HANDLE")
    if sub_handle:
        logger.info("--- SUBSCRIPTION SYNC ---")
        sync_subscriptions_to_watchlist(handle=sub_handle)

    watchlist = load_watchlist()
    seen_ids = load_digest_history()
    scoring_config = signal_profile.get("scoring", {})
    high_signal_threshold = scoring_config.get("high_signal_threshold", 7)
    digest_threshold = scoring_config.get("digest_threshold", 6)

    # Determine lookback — use first_run if no digest history exists
    history_path = Path("data/digest_history.json")
    try:
        with open(history_path) as f:
            history = json.load(f)
        has_previous = len(history.get("digests", [])) > 0
    except (FileNotFoundError, json.JSONDecodeError):
        has_previous = False

    lookback = config["fetch"]["lookback_days"] if has_previous else config["fetch"].get("first_run_lookback_days", 3)
    logger.info(f"Lookback: {lookback} days ({'daily' if has_previous else 'first run'})")

    # --- STAGE 1: FETCH ---
    logger.info("--- FETCH ---")
    posts, fetch_errors = fetch_all_posts(
        watchlist,
        lookback_days=lookback,
        max_posts_per_pub=config["fetch"]["max_posts_per_pub"],
        delay=config["fetch"]["delay_between_pubs_seconds"],
        seen_ids=seen_ids,
    )
    save_fetched_posts(posts, run_dir)

    if not posts:
        logger.info("No new posts found. Writing empty digest.")
        stats = {
            "publications_monitored": len(watchlist),
            "posts_scanned": 0,
            "high_signal_count": 0,
            "worth_a_look_count": 0,
            "fetch_errors": len(fetch_errors),
            "error_details": fetch_errors,
        }
        md = render_markdown([], stats, date=today)
        write_digest(md, config["output"]["digest_dir"], date=today)
        return

    # --- STAGE 2: SCORE ---
    logger.info("--- SCORE ---")
    scored = score_all_posts(posts, signal_profile=signal_profile, config=config)
    save_scored_posts(scored, run_dir)

    scoring_failures = len(posts) - len(scored)
    if not scored:
        logger.warning("All posts failed scoring. Writing fetch-only digest.")
        # Degraded mode: list posts without scores
        stats = {
            "publications_monitored": len(watchlist),
            "posts_scanned": len(posts),
            "high_signal_count": 0,
            "worth_a_look_count": 0,
            "fetch_errors": len(fetch_errors),
            "error_details": fetch_errors,
            "scoring_failures": scoring_failures,
        }
        md = render_markdown([], stats, date=today)
        write_digest(md, config["output"]["digest_dir"], date=today)
        return

    # --- STAGE 3: ENRICH ---
    logger.info("--- ENRICH ---")
    enriched, enrich_failed = enrich_top_posts(
        scored,
        threshold=high_signal_threshold,
        config=config,
    )

    # --- STAGE 4: DIGEST ---
    logger.info("--- DIGEST ---")
    entries = build_digest_entries(
        scored,
        enriched,
        high_signal_threshold=high_signal_threshold,
        digest_threshold=digest_threshold,
    )

    high_signal_count = sum(1 for e in entries if e.tier == "high_signal")
    worth_a_look_count = sum(1 for e in entries if e.tier == "worth_a_look")

    stats = {
        "publications_monitored": len(watchlist),
        "posts_scanned": len(posts),
        "high_signal_count": high_signal_count,
        "worth_a_look_count": worth_a_look_count,
        "fetch_errors": len(fetch_errors),
        "error_details": fetch_errors,
        "scoring_failures": scoring_failures,
        "enrichment_failures": len(enrich_failed),
    }

    md = render_markdown(entries, stats, date=today)
    digest_path = write_digest(md, config["output"]["digest_dir"], date=today)

    # Send to Zapier webhook (non-blocking — digest is already saved)
    webhook_url = config["output"].get("zapier_webhook_url")
    if webhook_url:
        send_to_zapier(md, entries, stats, webhook_url, date=today)

    # Email delivery (non-blocking)
    delivery_config = config.get("delivery", {})
    if delivery_config.get("enabled", False):
        send_digest_email(md, entries, stats, delivery_config, date=today)

    # Update history
    update_digest_history(entries, len(posts), date=today)

    # Check for reshares from previous digests (feedback loop)
    feedback_config = config.get("feedback", {})
    if feedback_config.get("enabled", True):
        substack_url = config.get("user", {}).get("substack_url") or os.getenv("SUBSTACK_URL")
        if substack_url:
            logger.info("--- FEEDBACK ---")
            reshares = check_for_reshares(substack_url)
        else:
            logger.warning("No SUBSTACK_URL configured — skipping feedback check")

    # Summary
    logger.info(f"=== Pipeline complete ===")
    logger.info(f"  Posts scanned: {len(posts)}")
    logger.info(f"  HIGH SIGNAL: {high_signal_count}")
    logger.info(f"  WORTH A LOOK: {worth_a_look_count}")
    logger.info(f"  Enrichment failures: {len(enrich_failed)}")
    logger.info(f"  Digest: {digest_path}")


if __name__ == "__main__":
    main()
