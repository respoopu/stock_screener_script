# Short Squeeze Screener

A Python-based stock screener that identifies potential short squeeze candidates and delivers daily alerts via Telegram.

## Prerequisites

- Python 3.10+
- [Financial Modeling Prep (FMP) API key](https://financialmodelingprep.com/) (free tier: 250 calls/day)
- Telegram bot token and chat ID

## Setup

### 1. Install dependencies

```bash
cd short_squeeze_screener
pip install -r requirements.txt
```

### 2. Get an FMP API key

1. Go to https://financialmodelingprep.com/ and create an account
2. Copy your API key from the dashboard

### 3. Create a Telegram bot

1. Open Telegram and message `@BotFather`
2. Send `/newbot` and follow the prompts
3. Copy the bot token
4. Start a conversation with your bot (send any message)
5. Visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` and find your `chat_id`

### 4. Configure credentials

Set environment variables (recommended):

```bash
export FMP_API_KEY="your_fmp_api_key"
export TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
export TELEGRAM_CHAT_ID="your_telegram_chat_id"
```

Or edit the placeholder values directly in `config.py`.

## Usage

### Run manually

```bash
python main.py
```

### Schedule with cron (macOS/Linux)

Run daily at 6:00 AM EST on weekdays:

```bash
crontab -e
```

Add:

```
0 6 * * 1-5 cd /path/to/short_squeeze_screener && /usr/bin/python3 main.py >> /var/log/screener.log 2>&1
```

## Screening Criteria

| Filter | Threshold |
|--------|-----------|
| Market Cap | $100M - $10B |
| Short Interest | >= 20% of float |
| Days to Cover | >= 5 days |
| Float | <= 50M shares |
| Volume Spike | >= 2x 20-day average |

## Ranking

Candidates are scored 0-100 using weighted factors:

- Short Interest %: 30%
- Days to Cover: 25%
- Volume Spike: 25%
- Float Size (lower = better): 20%

## Known Limitations

- **Short interest data**: FMP's free tier may not include short interest for all stocks. The screener tries multiple endpoints and skips stocks where data is unavailable.
- **API rate limit**: The screener uses ~52 API calls per run (well within the 250/day free tier). Avoid running more than once per day on the free tier.
- **Data freshness**: Short interest data is published bi-monthly by FINRA and may lag by several days.

## Project Structure

```
short_squeeze_screener/
├── config.py              # API keys, thresholds, logging setup
├── data_fetcher.py        # FMP API interaction with retry logic
├── screener.py            # Filtering pipeline and ranking
├── telegram_notifier.py   # Telegram message delivery
├── main.py                # Entry point / orchestrator
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## Disclaimer

This screener is for educational and informational purposes only. It is not financial advice. Short squeeze trading is highly speculative and risky. Always do your own research.
