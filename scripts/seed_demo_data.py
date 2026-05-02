from __future__ import annotations

from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "services" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from decimal import Decimal

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import AnalyticsSnapshot, BacktestRun, JournalEntry, Strategy, Trade, TradeContext, User


def seed() -> None:
    db = SessionLocal()
    try:
        user = db.execute(select(User).where(User.email == "demo@trademirror.local")).scalar_one_or_none()
        if user is None:
            user = User(email="demo@trademirror.local", full_name="TradeMirror Demo")
            db.add(user)
            db.flush()

        strategy_specs = [("NQ Mean Reversion", "NQ", "mean_reversion"), ("BTC Breakout Scalping", "BTCUSD", "scalping")]
        strategies: dict[str, Strategy] = {}
        for name, symbol, style in strategy_specs:
            strategy = db.execute(select(Strategy).where(Strategy.user_id == user.id, Strategy.name == name)).scalar_one_or_none()
            if strategy is None:
                strategy = Strategy(user_id=user.id, name=name, symbol=symbol, style=style, instrument="futures")
                db.add(strategy)
                db.flush()
            strategies[name] = strategy

        existing = db.query(Trade).filter(Trade.user_id == user.id).count()
        if existing < 40:
            now = datetime.now(timezone.utc)
            for i in range(40):
                strat = strategies["NQ Mean Reversion"] if i % 2 == 0 else strategies["BTC Breakout Scalping"]
                entry = now - timedelta(days=i + 1, hours=i % 6)
                exit_time = entry + timedelta(minutes=25 + (i % 30))
                side = "long" if i % 3 else "short"
                entry_price = Decimal("15000") + Decimal(i * 7)
                exit_price = entry_price + (Decimal("15") if side == "long" else Decimal("-12"))
                pnl = (exit_price - entry_price) * Decimal("1") if side == "long" else (entry_price - exit_price) * Decimal("1")
                trade = Trade(user_id=user.id, strategy_id=strat.id, source_type="backtest" if i < 25 else "live", instrument="futures" if i % 2 == 0 else "crypto", symbol=strat.symbol or "UNK", side=side, entry_time=entry, exit_time=exit_time, entry_price=entry_price, exit_price=exit_price, quantity=Decimal("1"), fees=Decimal("2.5"), slippage=Decimal("0.5"), pnl=pnl, r_multiple=Decimal("1.2"), planned_risk=Decimal("100"), actual_risk=Decimal("95"), order_type="market", session_label="ny_open" if i % 2 == 0 else "asia", setup_tags=["pullback", "trend"], notes="Seeded trade")
                db.add(trade)
                db.flush()
                if i % 5 != 0:
                    db.add(TradeContext(trade_id=trade.id, trend_regime="trending_up", volatility_regime="medium", macro_event_nearby=False, liquidity_score=Decimal("0.78"), context_payload={"seed": True}))

        if db.query(JournalEntry).filter(JournalEntry.user_id == user.id).count() < 10:
            first_trade = db.query(Trade).filter(Trade.user_id == user.id).first()
            for i in range(10):
                db.add(JournalEntry(user_id=user.id, trade_id=first_trade.id if first_trade else None, strategy_id=strategies["NQ Mean Reversion"].id, text=f"Demo journal note {i+1}", title=f"Session review {i+1}", emotion_tags=["calm"], mistake_tags=["late_entry"]))

        if db.query(BacktestRun).filter(BacktestRun.user_id == user.id).count() == 0:
            db.add(BacktestRun(user_id=user.id, strategy_id=strategies["NQ Mean Reversion"].id, name="Q1 Replay", parameters={"window": 20}, summary_stats={"win_rate": 0.56}))

        if db.query(AnalyticsSnapshot).filter(AnalyticsSnapshot.user_id == user.id).count() < 2:
            db.add(AnalyticsSnapshot(user_id=user.id, strategy_id=strategies["NQ Mean Reversion"].id, snapshot_type="performance_summary", payload={"placeholder": True}))
            db.add(AnalyticsSnapshot(user_id=user.id, strategy_id=strategies["BTC Breakout Scalping"].id, snapshot_type="regime_stats", payload={"placeholder": True}))

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
