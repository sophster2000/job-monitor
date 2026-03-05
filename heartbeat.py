"""
Daily heartbeat — sends a WhatsApp summary of the last 24 hours.
Run every morning at 9am Amsterdam time via GitHub Actions.
"""
from storage import get_stats_last_24h
from notifier import send_message


def main():
    stats = get_stats_last_24h()
    runs = stats["runs"]
    new_jobs = stats["new_jobs"]
    matched_jobs = stats["matched_jobs"]

    if runs == 0:
        status_line = "No runs completed in the last 24 hours — something may be wrong!"
    else:
        status_line = f"All good! Ran {runs}x in the last 24 hours."

    body = (
        f"Job Monitor — Daily Update\n"
        f"{status_line}\n"
        f"New jobs scanned: {new_jobs}\n"
        f"Matches sent to you: {matched_jobs}"
    )

    send_message(body)
    print(f"[Heartbeat] Sent — {runs} runs, {new_jobs} new jobs, {matched_jobs} matches.")


if __name__ == "__main__":
    main()
