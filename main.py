"""
Short Squeeze Screener - Main Entry Point

Scans the market for small/mid-cap stocks meeting short squeeze criteria,
ranks candidates by squeeze potential, and sends daily alerts via Telegram.

Usage:
    python main.py
"""

import sys
from datetime import datetime

from config import (
    SCREENING_CONFIG,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    setup_logging,
)
from data_fetcher import get_stock_universe
from screener import format_candidate_report, rank_candidates, screen_for_squeeze_candidates
from telegram_notifier import format_daily_alert, send_no_candidates_alert, send_telegram_message


def validate_config() -> list[str]:
    """
    Check that all required configuration values are set.
    Returns a list of error messages (empty if valid).
    """
    errors = []
    if TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        errors.append("TELEGRAM_BOT_TOKEN is not set. Set the TELEGRAM_BOT_TOKEN environment variable or update .env.")
    if TELEGRAM_CHAT_ID == "YOUR_TELEGRAM_CHAT_ID_HERE":
        errors.append("TELEGRAM_CHAT_ID is not set. Set the TELEGRAM_CHAT_ID environment variable or update .env.")
    return errors


def main():
    """
    Main execution flow:
    1. Setup logging and validate configuration
    2. Fetch stock universe from Yahoo Finance screeners
    3. Screen for squeeze candidates
    4. Rank candidates by squeeze score
    5. Format and send Telegram alert
    """
    logger = setup_logging()
    scan_date = datetime.now().strftime("%Y-%m-%d")

    logger.info("=" * 50)
    logger.info("Short Squeeze Screener - %s", scan_date)
    logger.info("=" * 50)

    # Validate configuration
    config_errors = validate_config()
    if config_errors:
        for error in config_errors:
            logger.error(error)
        logger.error("Configuration incomplete. Exiting.")
        sys.exit(1)

    # Step 1: Fetch stock universe
    logger.info("Fetching stock universe...")
    symbols = get_stock_universe()
    if not symbols:
        logger.error("Failed to fetch stock universe or no stocks found. Exiting.")
        sys.exit(1)
    logger.info("Universe: %d symbols collected", len(symbols))

    # Step 2: Screen for squeeze candidates
    logger.info("Screening for squeeze candidates...")
    candidates = screen_for_squeeze_candidates(
        symbols=symbols,
        config=SCREENING_CONFIG,
    )
    logger.info("Candidates: %d stocks passed all filters", len(candidates))

    # Step 3: Rank and send alert
    if candidates:
        ranked = rank_candidates(candidates)

        # Format report
        report_parts = [format_candidate_report(c) for c in ranked]
        report_text = "\n\n".join(report_parts)
        message = format_daily_alert(report_text, len(ranked), scan_date)

        # Send via Telegram
        logger.info("Sending Telegram alert with %d candidates...", len(ranked))
        success = send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message)
        if success:
            logger.info("Alert sent successfully")
        else:
            logger.error("Failed to send Telegram alert")
    else:
        logger.info("No candidates found. Sending notification...")
        success = send_no_candidates_alert(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, scan_date)
        if success:
            logger.info("No-candidates notification sent")
        else:
            logger.error("Failed to send no-candidates notification")

    # Summary
    logger.info("-" * 50)
    logger.info("Scan completed at %s", datetime.now().strftime("%H:%M:%S"))
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
