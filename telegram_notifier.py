"""
Telegram notification module for Short Squeeze Screener.
Handles message formatting, splitting, and delivery via the Telegram Bot API.
"""

import logging

import requests

logger = logging.getLogger("short_squeeze_screener.telegram_notifier")

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"
MAX_MESSAGE_LENGTH = 4096


def _split_message(message: str, max_length: int = MAX_MESSAGE_LENGTH) -> list[str]:
    """
    Split a message into chunks that fit within Telegram's character limit.
    Splits on separator lines to keep candidate reports intact.
    """
    if len(message) <= max_length:
        return [message]

    separator = "\u2501" * 22
    parts = message.split(separator)
    chunks = []
    current_chunk = ""

    for part in parts:
        # Reconstruct with separator
        piece = part if not current_chunk else separator + part

        if len(current_chunk) + len(piece) <= max_length:
            current_chunk += piece
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = part.strip()

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    # Final safety: split any chunk still over the limit at newline boundaries
    final_chunks = []
    for chunk in chunks:
        if len(chunk) <= max_length:
            final_chunks.append(chunk)
        else:
            lines = chunk.split("\n")
            sub_chunk = ""
            for line in lines:
                if len(sub_chunk) + len(line) + 1 <= max_length:
                    sub_chunk += line + "\n"
                else:
                    if sub_chunk.strip():
                        final_chunks.append(sub_chunk.strip())
                    sub_chunk = line + "\n"
            if sub_chunk.strip():
                final_chunks.append(sub_chunk.strip())

    return final_chunks if final_chunks else [message[:max_length]]


def send_telegram_message(bot_token: str, chat_id: str, message: str) -> bool:
    """
    Send a message via Telegram Bot API.
    Handles message length limits by splitting long messages.
    Returns True if all parts sent successfully.
    """
    chunks = _split_message(message)
    all_success = True

    for i, chunk in enumerate(chunks, 1):
        if len(chunks) > 1:
            logger.debug("Sending message part %d/%d (%d chars)", i, len(chunks), len(chunk))

        url = TELEGRAM_API_URL.format(token=bot_token)
        payload = {
            "chat_id": chat_id,
            "text": chunk,
        }

        success = False
        for attempt in range(2):  # Single retry
            try:
                response = requests.post(url, json=payload, timeout=30)
                data = response.json()

                if data.get("ok"):
                    success = True
                    break
                else:
                    logger.error(
                        "Telegram API error: %s (code: %s)",
                        data.get("description", "unknown"),
                        data.get("error_code", "?"),
                    )
                    # Don't retry on client errors (bad token, wrong chat id)
                    error_code = data.get("error_code", 0)
                    if 400 <= error_code < 500:
                        break

            except requests.exceptions.RequestException as e:
                logger.error("Telegram request failed (attempt %d): %s", attempt + 1, e)

        if not success:
            all_success = False

    return all_success


def format_daily_alert(report_text: str, candidate_count: int, scan_date: str) -> str:
    """
    Compose the full daily alert message.

    Takes a pre-formatted report string from screener.format_candidate_report().
    """
    header = (
        "\U0001f4ca SHORT SQUEEZE SCREENER\n"
        f"\U0001f4c5 {scan_date}\n"
        f"\n"
        f"Found {candidate_count} candidate{'s' if candidate_count != 1 else ''} meeting criteria:\n"
    )

    footer = (
        "\n\n"
        "\u26a0\ufe0f This is not financial advice.\n"
        "Always do your own research."
    )

    return header + "\n" + report_text + footer


def send_no_candidates_alert(bot_token: str, chat_id: str, scan_date: str) -> bool:
    """Send notification when no candidates are found."""
    message = (
        "\U0001f4ca SHORT SQUEEZE SCREENER\n"
        f"\U0001f4c5 {scan_date}\n"
        f"\n"
        "No stocks met all screening criteria today.\n"
        f"\n"
        "\u26a0\ufe0f This is not financial advice.\n"
        "Always do your own research."
    )
    return send_telegram_message(bot_token, chat_id, message)
