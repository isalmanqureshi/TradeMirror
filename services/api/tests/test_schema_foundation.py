import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import importlib.util

from app.db.base import Base
from app.models import Strategy, Trade, TradeContext, User
from app.schemas import TradeRead, UserRead


def test_expected_tables_registered() -> None:
    expected = {
        "users",
        "strategies",
        "trades",
        "trade_context",
        "journal_entries",
        "backtest_runs",
        "analytics_snapshots",
    }
    assert expected.issubset(set(Base.metadata.tables.keys()))


def test_models_and_relationships_configured() -> None:
    user = User(email="u@example.com")
    strategy = Strategy(user_id=uuid.uuid4(), name="test")
    trade = Trade(
        user_id=uuid.uuid4(),
        strategy_id=None,
        source_type="live",
        instrument="futures",
        symbol="NQ",
        side="long",
        entry_time=datetime.now(timezone.utc),
        entry_price=Decimal("1.0"),
    )
    context = TradeContext(trade_id=uuid.uuid4())

    assert user.strategies is not None
    assert strategy.trades is not None
    assert trade.trade_context is None
    assert context.trade is None


def test_schema_from_attributes() -> None:
    class Obj:
        id = uuid.uuid4()
        email = "demo@example.com"
        full_name = "Demo"
        created_at = datetime.now(timezone.utc)
        updated_at = datetime.now(timezone.utc)

    out = UserRead.model_validate(Obj())
    assert out.email == "demo@example.com"


def test_trade_schema_from_attributes() -> None:
    class T:
        id = uuid.uuid4()
        user_id = uuid.uuid4()
        strategy_id = None
        source_type = "paper"
        instrument = "crypto"
        symbol = "BTCUSD"
        side = "short"
        entry_time = datetime.now(timezone.utc)
        exit_time = None
        entry_price = Decimal("100.0")
        exit_price = None
        quantity = None
        fees = Decimal("0")
        slippage = None
        pnl = None
        r_multiple = None
        planned_risk = None
        actual_risk = None
        order_type = None
        session_label = None
        setup_tags = None
        notes = None
        created_at = datetime.now(timezone.utc)
        updated_at = datetime.now(timezone.utc)

    assert TradeRead.model_validate(T()).symbol == "BTCUSD"


def test_seed_script_importable() -> None:
    script_path = Path(__file__).resolve().parents[3] / "scripts" / "seed_demo_data.py"
    spec = importlib.util.spec_from_file_location("seed_demo_data", script_path)
    assert spec is not None and spec.loader is not None
