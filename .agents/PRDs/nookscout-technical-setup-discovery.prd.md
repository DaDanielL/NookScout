# NookScout Technical Setup Discovery

## Problem Statement

Beginner to intermediate, self-directed swing traders with zero to moderate market knowledge struggle to identify which liquid stocks are worth watching and how to combine technical signals into structured trade plans. They often make decisions from scattered chart data, social media noise, or incomplete rationale instead of beginner-friendly setup ideas with clear entry, invalidation, target, and risk/reward context.

## Key Hypothesis

We believe ranked technical swing setup discovery will help beginner to intermediate swing traders identify higher-quality stocks to watch and understand the rationale behind structured bullish trade-plan ideas.
We'll know we're right when active users create or review at least 3 structured setup ideas per week and 95% of generated setup ideas include complete technical rationale.

## Users

**Primary User**: Beginner to intermediate, self-directed swing traders with zero to moderate market knowledge who trade liquid U.S. stocks over multi-day to multi-week time horizons and want help finding setups, understanding technical rationale, and making more structured decisions without becoming full-time analysts.

**Job to Be Done**: When I am deciding what stocks to watch and create a trade plan for this week, I want NookScout to surface and explain high-quality swing setup ideas based on technical market indicators, so I can make structured trading decisions with confidence.

**Non-Users**: Day traders, professional portfolio managers, automated trading system users, options-first traders, crypto/forex traders, and users seeking guaranteed returns, direct buy/sell instructions, or personalized financial advice.

## Solution

NookScout will scan either a predefined liquid-stock universe or a user-defined watchlist, rank beginner-friendly bullish long swing setup ideas, and present each idea as a simple summary card with expandable technical detail. Each setup will include a read-only trade-plan visualization on an interactive daily price chart with entry, stop/invalidation, and target zones, plus educational rationale explaining why the setup may be worth watching and why it might fail.

### MVP Scope

| Priority | Capability | Rationale |
|----------|------------|-----------|
| Must | Scout Mode | Scans a predefined liquid-stock universe and displays ranked setup ideas for users who do not know what to watch. |
| Must | Watchlist Mode | Lets users create saved watchlists, add/remove tickers, and rank setup ideas only within the selected watchlist. |
| Must | Liquid stock universe filter | Limits Scout Mode to beginner-friendlier U.S.-listed stocks using rules such as price above $5, average volume above 1M shares/day, dollar volume above $20M-$50M/day, market cap above $1B, and exclusions for OTC or highly illiquid names. |
| Must | Bullish long setup ideas only | Keeps the MVP beginner-appropriate and avoids short-selling complexity. Weak tickers should be labeled as "No Clear Setup" or "Avoid / Wait" rather than bearish trade ideas. |
| Must | Technical setup scoring | Evaluates trend, 20/50/200 moving averages, support/resistance, RSI, MACD, volume/relative volume, ATR volatility, and relative strength vs SPY/QQQ. |
| Must | Ranked setup card summary | Displays rank, ticker, company name, current price, setup type, confidence label, risk/reward estimate, and one-sentence thesis summary. |
| Must | Expanded setup detail | Shows full thesis, trend context, support/resistance rationale, RSI/MACD interpretation, volume confirmation, ATR/volatility context, relative strength, entry zone, stop/invalidation area, target area, and why the setup might fail. |
| Must | Annotated price chart | Displays daily price candles with read-only entry zone, stop/invalidation area, target area, and current price marker. |
| Must | Chart range controls | Lets users switch between 1M, 3M, 6M, and 1Y chart ranges, defaulting to 3M. |
| Must | Expected holding window | Labels each setup with an expected swing holding window, generally 3 to 20 trading days. |
| Should | Beginner-friendly signal explanations | Explains technical signals in plain language without overwhelming the default card view. |
| Should | Setup type labels | Uses simple labels such as Breakout Watch, Pullback Setup, Trend Continuation, Reversal Watch, and No Clear Setup. |
| Won't | Trade journaling | Deferred to a later PRD. |
| Won't | Fundamental analysis agents | Deferred until the technical setup discovery loop is validated. |
| Won't | Catalyst, news, sentiment, or alternative-data agents | Deferred because these sources add noise, cost, and validation complexity. |
| Won't | Bull/bear debate validation modules | Explicitly out of scope for MVP and needs further product exploration. |
| Won't | Backtesting or automated recommendation evaluation | Deferred until the product has enough structured setup and outcome data to define evaluation criteria. |
| Won't | Brokerage integration or automated trading | Out of scope for MVP due to safety, compliance, and complexity. |

## Success Metrics

| Metric | Target | How Measured |
|--------|--------|--------------|
| Weekly setup engagement | Active users create or review at least 3 structured setup ideas per week | Product analytics event for setup card creation, expansion, or review |
| Setup completeness | 95% of generated setup ideas include thesis summary, setup type, confidence, risk/reward, entry zone, stop/invalidation area, target area, supporting technical signals, and failure case | Automated completeness check on setup outputs |
| Scout Mode usefulness | Users expand or save at least 1 setup idea from Scout Mode per active week | Product analytics for card expansion and save events |
| Watchlist Mode usefulness | Users create at least 1 saved watchlist and review ranked setup ideas from it | Product analytics for watchlist creation and watchlist analysis events |
| User clarity | Users report increased confidence and clarity after reviewing setup rationale | Lightweight in-product survey after setup detail review |
| Weekly retention | Users return weekly to review ranked setup ideas or saved watchlists | Weekly active user cohort retention |

## Open Questions

- [ ] Which market data provider should power current prices, historical daily candles, volume, and technical indicators?
- [ ] Should NookScout compute technical indicators internally or rely on a provider's precomputed indicators?
- [ ] What exact liquidity rules should define the predefined stock universe for v1?
- [ ] How many setup ideas should Scout Mode show by default before the interface becomes overwhelming?
- [ ] How should confidence labels be defined without implying certainty or personalized financial advice?
- [ ] What legal/compliance language is required to position setup ideas as educational information rather than financial advice?
- [ ] Should the MVP include sector-relative strength, or only relative strength vs SPY/QQQ?
- [ ] Should users be able to save individual setup ideas in MVP, or only save watchlists?
- [ ] What constraints exist for budget, data licensing, timeline, hosting, and model/API usage?

## Implementation Phases

| # | Phase | Description | Status | Depends |
|---|-------|-------------|--------|---------|
| 1 | Market Data Foundation | Select data source, retrieve current prices and daily historical candles, and define the predefined liquid-stock universe. | pending | - |
| 2 | Technical Indicator Pipeline | Compute or retrieve moving averages, support/resistance, RSI, MACD, volume/relative volume, ATR, and relative strength. | pending | 1 |
| 3 | Setup Scoring Engine | Score eligible tickers, classify beginner-friendly bullish setup types, and identify no-clear-setup cases. | pending | 2 |
| 4 | Setup Synthesis | Generate ranked educational setup cards with summary fields, expanded rationale, setup levels, confidence, risk/reward, and failure cases. | pending | 3 |
| 5 | Scout Mode UI | Display ranked setup ideas from the predefined universe in a beginner-friendly dashboard. | pending | 4 |
| 6 | Watchlist Mode UI | Let users create saved watchlists, manage tickers, and run ranked setup discovery against selected watchlists. | pending | 4 |
| 7 | Annotated Chart Experience | Render daily price charts with 1M, 3M, 6M, and 1Y ranges plus entry, stop/invalidation, target, and current price overlays. | pending | 4 |
| 8 | MVP Instrumentation | Track setup engagement, setup completeness, Scout Mode usefulness, Watchlist Mode usefulness, clarity feedback, and weekly retention. | pending | 5 |

## Future Extension Considerations

Future journaling, fundamental, catalyst, alternative-data, and validation agents should plug into the same structured setup schema rather than replacing the MVP workflow. The MVP should store setup inputs, indicator values, setup type, generated rationale, confidence factors, chart levels, scoring version, and user interactions so later PRDs can add trade journals, outcome review, and evaluation agents without redesigning setup discovery from scratch.

---

*Generated: 2026-05-03 04:47 EDT*
*Status: DRAFT - needs validation*
