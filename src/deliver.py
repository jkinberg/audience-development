"""Email delivery: convert markdown digest to HTML and send via Gmail SMTP."""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import markdown2
from dotenv import load_dotenv

from src.models import DigestEntry

load_dotenv()
logger = logging.getLogger("pipeline.deliver")

EMAIL_CSS = """
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; line-height: 1.6; color: #1a1a1a; max-width: 640px; margin: 0 auto; padding: 20px; background: #ffffff; }
h1 { font-size: 22px; border-bottom: 2px solid #e0e0e0; padding-bottom: 8px; margin-bottom: 4px; }
h1 + p { font-size: 14px; color: #666; margin-top: 0; }
h2 { font-size: 18px; margin-top: 28px; margin-bottom: 4px; }
h2 a { color: #1a6fb5; text-decoration: none; }
h2 a:hover { text-decoration: underline; }
blockquote { border-left: 3px solid #c0c0c0; margin: 12px 0; padding: 4px 16px; color: #444; font-style: italic; }
hr { border: none; border-top: 1px solid #e0e0e0; margin: 24px 0; }
em { color: #666; }
ul, ol { padding-left: 20px; }
li { margin-bottom: 4px; }
p { margin: 8px 0; }
"""


def markdown_to_html(md_text: str) -> str:
    """Convert markdown digest to styled HTML email body."""
    html_body = markdown2.markdown(
        md_text,
        extras=["fenced-code-blocks", "cuddled-lists", "header-ids"],
    )
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>{EMAIL_CSS}</style></head>
<body>{html_body}</body>
</html>"""


def send_digest_email(
    markdown: str,
    entries: list[DigestEntry],
    stats: dict,
    config: dict,
    date: str,
) -> bool:
    """Send digest as HTML email via Gmail SMTP. Returns True on success."""
    gmail_address = os.getenv("GMAIL_ADDRESS")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")

    if not gmail_address or not gmail_password:
        logger.warning("Gmail credentials not set — skipping email delivery")
        return False

    to_email = config.get("to_email", gmail_address)
    high_signal_count = stats.get("high_signal_count", 0)

    subject_template = config.get(
        "subject_template",
        "Signal Pipeline — {date} — {high_signal_count} high signal"
    )
    subject = subject_template.format(date=date, high_signal_count=high_signal_count)

    # Skip empty digests if configured
    if high_signal_count == 0 and config.get("skip_empty", False):
        logger.info("No high signal posts — skipping email (skip_empty=true)")
        return True

    # Build email
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = gmail_address
    msg["To"] = to_email

    # Plain text fallback
    msg.attach(MIMEText(markdown, "plain"))

    # HTML version
    html = markdown_to_html(markdown)
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_address, gmail_password)
            server.sendmail(gmail_address, to_email, msg.as_string())
        logger.info(f"Digest emailed to {to_email}")
        return True
    except Exception as e:
        logger.warning(f"Email delivery failed (non-blocking): {e}")
        return False
