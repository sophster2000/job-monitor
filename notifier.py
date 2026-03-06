"""
Sends WhatsApp notifications via Twilio for matching jobs.
"""
from twilio.rest import Client
from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM, TWILIO_WHATSAPP_TO

_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
MAX_BODY = 1500  # Twilio WhatsApp limit is 1600 chars; leave headroom


def send_message(body: str) -> None:
    """Send a plain WhatsApp message, truncating if necessary."""
    if len(body) > MAX_BODY:
        body = body[:MAX_BODY - 3] + "..."
    _client.messages.create(
        from_=TWILIO_WHATSAPP_FROM,
        to=TWILIO_WHATSAPP_TO,
        body=body,
    )


def send_whatsapp(job: dict, score: float, reason: str) -> None:
    title = job.get("title", "Unknown role")
    company = job.get("company", "")
    location = job.get("location", "")
    url = job.get("url", "")
    source = job.get("source", "")

    lines = [
        f"Job Match ({score:.1f}/10) via {source}",
        f"*{title}*",
    ]
    if company:
        lines.append(f"Company: {company}")
    if location:
        lines.append(f"Location: {location}")
    # Truncate reason if needed
    reason_truncated = reason[:300] + "..." if len(reason) > 300 else reason
    lines.append(f"Why: {reason_truncated}")
    if url:
        lines.append(f"Link: {url}")

    send_message("\n".join(lines))
    print(f"[Notifier] Sent WhatsApp for: {title} ({score:.1f}/10)")
