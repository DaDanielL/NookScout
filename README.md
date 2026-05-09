# NookScout

NookScout is a local-first FastAPI application for educational technical setup discovery in liquid U.S. stocks. The MVP will scan a predefined universe or saved watchlists, rank bullish swing setup ideas, and explain each idea with deterministic technical context before any LLM rationale is generated.

The product is for learning and research. It is not brokerage software, does not place trades, and does not provide personalized financial advice.

## Local Setup

Install Python dependencies:

```bash
uv sync
```

Create a local environment file when you are ready to run with real provider settings:

```bash
cp .env.example .env
```

Keep real API keys and database credentials only in `.env`.

## Backend Commands

Start the backend development server:

```bash
uv run fastapi dev app/main.py
```

Run the placeholder local scheduler entrypoint:

```bash
uv run python -m app.jobs.scheduler
```

Run backend validation:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest
```

## Health Check

With the backend running, verify the API:

```bash
curl http://127.0.0.1:8000/health
```

The response includes non-secret operational metadata such as status, app name, environment, selected market data provider, timezone, and a checked timestamp.

## Market Data

The MVP provider decision is documented in [docs/market-data-providers.md](docs/market-data-providers.md). Provider access must go through future adapters under `app/market_data/`; scoring, indicators, persistence, and UI code should not call provider APIs directly.

## AI Workflow

Project planning and implementation artifacts live under `.agents/`. Start with [.agents/README.md](.agents/README.md) for the Codex workflow layer.

## Educational Disclaimer

NookScout output is educational, general-market research support for a local personal user. It should not be interpreted as individualized investment advice, direct buy/sell instructions, guaranteed outcomes, or a substitute for independent judgment.
