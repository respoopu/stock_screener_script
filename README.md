# SqueezeRadar

A fully automated stock screening engine that scans US equity markets every night for potential short squeeze setups. It filters small and mid-cap stocks through five technical criteria, ranks candidates using a weighted scoring algorithm, and delivers daily Telegram alerts.

## Prerequisites

- Python 3.10+
- Telegram bot token and chat ID

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Create a Telegram bot

1. Open Telegram and message `@BotFather`
2. Send `/newbot` and follow the prompts
3. Copy the bot token
4. Start a conversation with your bot (send any message)
5. Visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` and find your `chat_id`

### 3. Configure credentials

Create a `.env` file in the project root:

```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

Or set them as environment variables.

## Usage

### Run manually

```bash
python main.py
```

### Automated (GitHub Actions)

The included workflow runs every night at 9:30 PM SGT (13:30 UTC). Add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` as repository secrets under Settings > Secrets > Actions.

You can also trigger a run manually from the Actions tab.

## Screening Criteria

| Filter | Threshold |
|--------|-----------|
| Market Cap | $100M - $10B |
| Short Interest | >= 20% of float |
| Days to Cover | >= 5 days |
| Float | <= 50M shares |
| Volume Spike | >= 2x average |

## Ranking

Candidates are scored 0-100 using weighted factors:

- Short Interest %: 30%
- Days to Cover: 25%
- Volume Spike: 25%
- Float Size (lower = better): 20%

## Project Structure

```
├── .github/workflows/scan.yml  # GitHub Actions scheduled workflow
├── config.py                   # Thresholds, weights, logging setup
├── data_fetcher.py             # Yahoo Finance data retrieval
├── screener.py                 # Filtering pipeline and ranking
├── telegram_notifier.py        # Telegram message delivery
├── main.py                     # Entry point / orchestrator
├── requirements.txt            # Python dependencies
└── .env                        # Credentials (not tracked in git)
```

## Known Limitations

- **Data freshness**: Short interest data is published bi-monthly by FINRA and may lag by several days.
- **Universe size**: Yahoo Finance screeners return ~130 actively traded stocks per run. Stocks not surfaced by these screeners won't be evaluated.

## Disclaimer

This screener is for educational and informational purposes only. It is not financial advice. Short squeeze trading is highly speculative and risky. Always do your own research.
