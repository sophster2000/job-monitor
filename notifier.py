"""
Sends WhatsApp notifications via Twilio for matching jobs.
"""
from twilio.rest import Client
from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM, TWILIO_WHATSAPP_TO

_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def send_whatsapp(job: dict, score: float, reason: str) -> None:
    title = job.get("title", "Unknown role")
    company = job.get("company", "Unknown company")
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
    lines.append(f"Why: {reason}")
    if url:
        lines.append(f"Link: {url}")

    body = "\n".join(lines)

    _client.messages.create(
        from_=TWILIO_WHATSAPP_FROM,
        to=TWILIO_WHATSAPP_TO,
        body=body,
    )
    print(f"[Notifier] Sent WhatsApp for: {title} ({score:.1f}/10)")
