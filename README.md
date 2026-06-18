# InvestDash

A personal investment dashboard built with Flask, PostgreSQL, and live market data — combining user account management, a real-time stock watchlist, financial calculators, and a full paper-trading simulator into one web application.

Built as a course project for **財金APP實作與應用** at NKUST.

## Features

- **User accounts** — registration with email verification, secure login (bcrypt password hashing), forgot/reset password via email, and rate-limited auth routes
- **Live watchlist** — near real-time stock prices via the Finnhub API, with personal notes per stock and an embedded TradingView chart
- **Stock comparison** — compare up to three stocks side by side on one chart, with a best-performer indicator
- **Financial calculators** — stock return, compound interest, and loan payment calculators
- **Price alerts** — set a target price and get notified automatically when a stock crosses it
- **Financial news** — live headlines by category (general, forex, crypto, mergers)
- **Trading simulator** — paper-trade with $10,000 in virtual cash; track holdings, profit/loss, and full trade history
- **Stock research panel** — company profile, valuation, financial health metrics, a live TradingView technical analysis gauge, and company-specific news, all in one modal
- **Dark mode** — full light/dark theme support across every page

## Tech Stack

- **Backend:** Flask, Flask-Login, Flask-Bcrypt, Flask-Mail, Flask-Limiter
- **Database:** PostgreSQL via SQLAlchemy
- **Market data:** Finnhub API (quotes, company profiles, fundamentals, news)
- **Charts & widgets:** TradingView embeddable widgets (chart, technical analysis, symbol comparison)
- **Frontend:** Bootstrap 5, vanilla JavaScript, Jinja2 templates

## Setup

1. Clone the repo and create a virtual environment:
```bash
   git clone https://github.com/jevendonavon/investment-dashboard.git
   cd investment-dashboard
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
```

2. Create a `.env` file in the project root with:
SECRET_KEY=your-secret-key

DATABASE_URL=postgresql://username:password@localhost:5432/investment_dashboard

FINNHUB_API_KEY=your-finnhub-api-key

MAIL_USERNAME=your-gmail-address

MAIL_PASSWORD=your-gmail-app-password

3. Create the PostgreSQL database:
```bash
   sudo -u postgres psql -c "CREATE DATABASE investment_dashboard;"
```

4. Run the app:
```bash
   python run.py
```

5. Visit `http://127.0.0.1:5000`

## Project Structure

investment-dashboard/

├── app/

│   ├── init.py        # App factory

│   ├── models.py          # SQLAlchemy models

│   ├── routes.py          # All routes and API endpoints

│   ├── static/

│   │   ├── css/style.css

│   │   └── js/main.js

│   └── templates/         # Jinja2 templates

├── config.py               # App configuration (reads from .env)

├── run.py                  # Entry point

└── .env                     # Environment variables (not committed)

## Notes

This is a course project built for educational purposes. The trading simulator uses real live market prices but virtual cash only — no real money or brokerage integration is involved.
