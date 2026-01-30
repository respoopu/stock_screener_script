"""
Configuration for Short Squeeze Screener.
Loads from environment variables with fallback to placeholder defaults.
"""

import os
import logging
from pathlib import Path

from dotenv import load_dotenv

# Load .env file from the project directory
load_dotenv(Path(__file__).resolve().parent / ".env")

# --- Telegram Configuration ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "YOUR_TELEGRAM_CHAT_ID_HERE")

# --- Screening Thresholds ---
SCREENING_CONFIG = {
    "min_market_cap": 100_000_000,        # $100M
    "max_market_cap": 10_000_000_000,     # $10B
    "min_short_interest_pct": 20,          # 20% of float
    "min_days_to_cover": 5,                # 5 days
    "max_float_shares": 50_000_000,        # 50M shares
    "min_volume_spike_ratio": 2.0,         # 2x average volume
}

# --- Ranking Weights ---
RANKING_WEIGHTS = {
    "short_interest_pct": 0.30,
    "days_to_cover": 0.25,
    "volume_spike": 0.25,
    "float_size": 0.20,
}

# --- Data Settings ---
TICKER_FETCH_BATCH_SIZE = 20  # Symbols to fetch info for concurrently
TICKER_FETCH_DELAY = 0.5      # Seconds between batches to avoid throttling

# --- Logging ---
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_FILE = "screener.log"


def setup_logging() -> logging.Logger:
    """Configure logging for the application."""
    logger = logging.getLogger("short_squeeze_screener")
    logger.setLevel(logging.DEBUG)

    # Console handler - INFO level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    console_fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_fmt)

    # File handler - DEBUG level
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_fmt)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
