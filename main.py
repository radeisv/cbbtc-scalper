"""Scalper D — a fast, frequent, small-win cbBTC scalper for make.fun
(agent-fun/bars-replay/v1), built for btc-race-24h-20261118-1444.

Mission: trade often and bank small wins instead of waiting for one big
swing. The user asked for exactly this: quick buy/sell, a little PnL at a
time, many times. So the bot uses a short 45-minute average, enters on a
shallow 60 bps dip, and exits at the first sign the move is done — a 120 bps
take-profit, a 120 bps stop, or the price climbing 120 bps back above the
average. It re-enters immediately when the dip is still there after a
stop-out: no cooldown, no bounce filter, no hesitation. On the dev window
that produces 3 round trips in 24 hours, not 1.

How this config was picked (grid run in the build session, 2,880 combos on
the NEW dev window, SMA 10/20/30/45/60 x dip 20-80 bps x TP 40-150 bps x
stop 80-200 bps x sell-above 40-150 bps, exact engine fill math):
- Best by PnL alone was SMA 60 / dip 60 / TP 150 / stop 150: +$14.62, but
  only 2 trades (1 round trip), and its neighbours fall apart (dip 50:
  -$3.51; TP 190: -$18.55; SMA 45: -$19.17) — a one-trade knife edge, and
  under a synthetic -2% drift it loses -$17.24. Rejected: not a scalper,
  and not robust.
- Most frequent profitable config was SMA 45 / dip 40 / TP 100 / stop 80:
  10 trades (5 round trips), +$3.13 on the new window — but -$19.32 on the
  old window. Rejected: it only wins on one window.
- The config below is the best frequent config that is positive on BOTH
  windows: 6 trades on the new window, 3 on the old one, and the widest
  grid search found 22 configs with >=6 trades that are positive on both.
- Small-TP 40 bps variants top out at +$5.72 with 4 trades: a 40 bps win
  is about $4 gross against ~$1.20 of fees plus slippage per round trip,
  so cutting winners that short leaves almost nothing after costs.
- Bollinger entries lost -$67..-$132 and breakouts -$19..-$72 on the new
  window. The old Dip Buyer v2 (SMA 90 / dip 80 / TP 190) still makes
  +$17.25 on the new window but only 1 round trip — more money, not the
  fast trading the user asked for. The old v1 (SMA 360 / dip 30, sell at
  SMA +40) loses -$14.66 on the new window.

Trade log on the NEW dev window (real-bot replay, exact engine fill math,
confirmed twice with byte-identical action logs, sha
0232e4e2632365c24c29d9aa8abf0d2198092f9e48b2e5291eb04b2c86dedde4):
- buy  bar  60 @ $64,287.13, $1,000.00 in
- sell bar  68 @ $63,330.88, $984.34 out — stop-loss, -$15.66
- buy  bar  69 @ $63,513.48, $984.34 in — dip still there, straight back in
- sell bar  81 @ $64,292.92, $995.62 out — bounce banked, +$11.28
- buy  bar 133 @ $63,535.41, $995.62 in
- sell bar 401 @ $64,299.80, $1,006.79 out — +$11.17
Net +$6.79, 6 order trades, max drawdown 1.83% (limit 25%).
Neighbours all stay positive on the new window (dip 50: +$6.22; TP 100:
+$0.97; stop 150: +$11.25 but only 2 trades), so the config is a plateau
for PnL even though the exact trade count moves with the stop.

Robustness (same simulator): new window +$6.79; old window +$12.32;
synthetic +2% drift +$7.57 and -2% drift +$6.44 on the new window; at 2x
fees still +$4.10. Honest weak spot: on the OLD window a -2% drift turns
it to -$3.19, and the stop at 120 bps is the sensitive knob — stop 100
loses -$0.76 on the new window. The dev window itself is a slow downtrend
(BTC -2.80%, $65,083 -> $63,261; buy-and-hold -$31.63), so most of the
day offers only the one dip-recovery the bot rides from bar 133 to 401;
in a choppier live race it should trade more often than the 3 round trips
seen on dev, and in a steadier trend it will trade less. That is the
trade-off the user chose knowingly: less dev PnL than v2's +$17.25, in
exchange for fast, frequent trading.

Rules, per batch (one bar per batch), all integer math, fully deterministic:
- Keep a 45-bar (45-minute) simple moving average of closes, as a running
  integer sum — no floats anywhere in the decision.
- Decide nothing for the first 60 bars: the 45-bar average needs 15 bars
  to settle after it first forms before its dips mean anything. This
  warm-up is part of the tested strategy — the grid that picked this config
  used the same 60-bar warm-up, and dropping it to 45 changes the first
  entry by a bar and flips the whole run (verified: warm-up 45 gives
  -$1.92 with 4 trades on the new window instead of +$6.79 with 6).
- Flat and the close is at least 60 bps below the SMA: buy with ALL cash.
  No buys in the last 30 bars of a 1440-bar window.
- Holding: sell everything when the position is worth 120 bps over its
  cost (take-profit), 120 bps under its cost (stop-loss), or the close has
  climbed to 120 bps above the SMA (the dip has fully reverted — bank it
  even if the take-profit was not reached).
- Orders fill at the next bar's open, so every signal acts with one bar of
  lag; the thresholds are wide enough that this does not matter.
- max_slippage_bps is 100 (1%): a fill more than 1% past the close we
  decided on is refused rather than filled for almost nothing.

Protocol notes: the harness sends hello once, then one batch per minute
(each batch carries that minute's bar, the fills of the orders sent on the
previous batch, and the account), and this bot answers every batch with
exactly one reply echoing its seq and carrying its orders (at most one
order per reply here). During warm-up batches no orders are sent. No
network, no wall clock, no files outside the repository, no randomness:
the same bars always produce the same orders.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
BPS = 10_000

# --- strategy parameters: the frequent, robust scalper from the grid ---
SMA_BARS = 45            # 45-minute simple moving average of closes
WARMUP_BARS = 60         # no decisions before bar 60: SMA + 15 bars to settle
BUY_DIP_BPS = 60         # buy when the close is at least this far below the SMA
SELL_ABOVE_BPS = 120     # sell when the close has reverted this far above the SMA
TAKE_PROFIT_BPS = 120    # sell when the position is worth this far over its cost
STOP_BPS = 120           # sell when the position is worth this far under its cost
MAX_SLIPPAGE_BPS = 100
TAIL_BARS = 30           # no new buys this close to the end of a 1440-bar window
WINDOW_BARS = 1440


class FastScalper:
    """Rolling 45-bar SMA of closes, kept as an integer running sum."""

    def __init__(self):
        self.closes = []       # closes seen so far, ints at price_scale
        self.window_sum = 0    # sum of the last SMA_BARS closes

    def push(self, close):
        self.closes.append(close)
        self.window_sum += close
        if len(self.closes) > SMA_BARS:
            self.window_sum -= self.closes[-SMA_BARS - 1]

    def ready(self):
        return len(self.closes) >= WARMUP_BARS

    def _dip_bps(self, close):
        """(SMA - close) in bps of the SMA, cross-multiplied to stay in
        integers: dip_bps = (window_sum - SMA_BARS * close) * BPS / window_sum.
        Returns the numerator; compare against BUY_DIP_BPS * window_sum."""
        return (self.window_sum - SMA_BARS * close) * BPS

    def _sell_order(self, held):
        return [{"side": "sell", "symbol": SYMBOL, "qty": held.qty,
                 "max_slippage_bps": MAX_SLIPPAGE_BPS}]

    def on_batch(self, state, batch):
        fresh = False
        for bar in batch["bars"]:
            if bar["symbol"] == SYMBOL:
                self.push(int(bar["c"]))
                fresh = True
        # A batch with no CBBTC bar (a minute the recorder missed) carries
        # no new information: do not re-decide on a stale close, just wait
        # for the next bar. The dev window has no gaps, so this changes
        # nothing there; it only keeps race behaviour clean if a minute
        # is missed.
        if not fresh:
            return []
        if state.warming_up or not self.ready():
            return []
        close = state.close(SYMBOL)
        if close is None:
            return []
        held = state.positions.get(SYMBOL)
        if held is not None:
            # Exits, checked cheapest first: reversion, then take-profit,
            # then stop-loss. Any one of them sells everything.
            if close * SMA_BARS * BPS >= self.window_sum * (BPS + SELL_ABOVE_BPS):
                return self._sell_order(held)
            if state.value(SYMBOL, held.qty) * BPS >= held.cost * (BPS + TAKE_PROFIT_BPS):
                return self._sell_order(held)
            if state.value(SYMBOL, held.qty) * BPS <= held.cost * (BPS - STOP_BPS):
                return self._sell_order(held)
            return []
        # Entry: full-size dip buy, not in the tail of the window. No
        # bounce filter and no cooldown on purpose: after a stop-out the
        # dip is usually still there, and the re-entry is the trade that
        # pays (bars 68 -> 69 on dev). The stop is what limits the loss,
        # not hesitation.
        if state.seq >= state.warmup_bars + WINDOW_BARS - TAIL_BARS:
            return []
        if self._dip_bps(close) < BUY_DIP_BPS * self.window_sum:
            return []
        if state.cash < int(state.hello["fees"]["min_notional_quote_units"]):
            return []
        return [{"side": "buy", "symbol": SYMBOL, "notional_quote_units": state.cash,
                 "max_slippage_bps": MAX_SLIPPAGE_BPS}]


def main():
    makefun_bars.run(FastScalper().on_batch)


if __name__ == "__main__":
    main()
