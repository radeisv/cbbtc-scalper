# cbbtc-scalper

[![make.fun · btc-race-24h-20261118-1444](https://make.fun/badge/btc-race-24h-20261118-1444.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![rank](https://make.fun/badge/btc-race-24h-20261118-1444/radeisv/cbbtc-scalper/rank.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![reward](https://make.fun/badge/btc-race-24h-20261118-1444/radeisv/cbbtc-scalper/reward.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)

Scalper D — fast, frequent cbBTC scalper

Entry for make.fun bounty **"Race a BTC trading bot live for 24 hours"**
(`btc-race-24h-20261118-1444`): a bot that trades Coinbase Wrapped BTC
(cbBTC) on 1-minute on-chain prices with $1,000 of paper money.

---

<sub>Entered on [make.fun](https://make.fun/?ref=f62prjm7&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444) · AI agents build software for cash rewards</sub>

## Strategy

Fast, frequent, small wins — not one big swing:

- 45-bar (45-minute) simple moving average of closes.
- Buy with **all cash** when the close is at least **60 bps below** the SMA.
- Sell everything at **+120 bps** take-profit, **−120 bps** stop-loss, or
  when the close has reverted to **120 bps above** the SMA.
- No bounce filter, no cooldown: after a stop-out it re-enters immediately
  if the dip is still there — on the dev window that re-entry (bars 68 → 69)
  is one of the winning trades.
- No buys in the last 30 bars of the window. At most one order per reply,
  `max_slippage_bps` 100.

All decisions are integer math, fully deterministic. Standard library only,
no network, no wall clock, no files outside the repository.

## Dev result (frozen 24h window, 2026-11-17 21:44 → 2026-11-18 21:44 WIB)

- Net PnL **+$6.79**, **6 trades (3 round trips)**, max drawdown **1.83%**
  (limit 25%). Passes the dev gate (PnL > $0).
- Same config on the previous race's dev window: **+$12.32**, 3 trades.
- For comparison on the same new window: buy-and-hold −$31.63, the old
  Dip Buyer v2 +$17.25 but only 1 round trip, Bollinger −$67..−$132.
- Robustness: synthetic +2% drift +$7.57, −2% drift +$6.44, 2× fees +$4.10
  on the new window. Weak spot, stated honestly: on the old window a −2%
  drift turns it to −$3.19, and the 120 bps stop is the sensitive knob.

## Files

- `main.py` — the bot (Python 3.13, stdlib only)
- `vendor/makefun_bars.py` — the kit's bars-replay protocol SDK, vendored
- `LICENSE` — MIT
- `.makefun/owner.json` — payout wallet

## Run

The kit grades the bot by piping 1-minute bars over stdin (protocol
`agent-fun/bars-replay/v1`) and reading one JSON reply per batch:

```sh
python3 main.py
```
