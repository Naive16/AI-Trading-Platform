"""Tests validating Python models strictly conform to shared/schemas/*.schema.json."""
import json
from pathlib import Path

import jsonschema

from services.trading_engine.app.models.account import Account
from services.trading_engine.app.models.order import OrderRequest, OrderSide
from services.trading_engine.app.models.position import Position, PositionSide
from services.trading_engine.app.models.risk_decision import DecisionType, RiskDecision
from services.trading_engine.app.models.signal import Signal, SignalAction

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "shared" / "schemas"


def load_schema(schema_name: str) -> dict:
    """Load JSON schema from shared/schemas/."""
    schema_path = SCHEMAS_DIR / schema_name
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_signal_schema_conformance():
    """Verify Signal model JSON validates against signal.schema.json."""
    schema = load_schema("signal.schema.json")
    signal = Signal(
        symbol="XAUUSD",
        timeframe="M15",
        action=SignalAction.BUY,
        confidence=0.85,
        entry=2650.25,
        stopLoss=2640.25,
        takeProfit=2670.25,
        riskPercent=0.5,
        strategy="momentum_breakout",
    )
    signal_json = signal.model_dump(mode="json")
    jsonschema.validate(instance=signal_json, schema=schema)


def test_account_schema_conformance():
    """Verify Account model JSON validates against account.schema.json."""
    schema = load_schema("account.schema.json")
    account = Account(
        accountId="ACC-12345",
        currency="USD",
        balance=100000.0,
        equity=99500.0,
        margin=1000.0,
        freeMargin=98500.0,
        drawdownPercent=0.5,
    )
    account_json = account.model_dump(mode="json")
    jsonschema.validate(instance=account_json, schema=schema)


def test_order_schema_conformance():
    """Verify OrderRequest model JSON validates against order.schema.json."""
    schema = load_schema("order.schema.json")
    order = OrderRequest(
        signalId="00000000-0000-0000-0000-000000000001",
        symbol="XAUUSD",
        side=OrderSide.BUY,
        volume=1.0,
        entry=2650.25,
        stopLoss=2640.25,
        takeProfit=2670.25,
    )
    order_json = order.model_dump(mode="json")
    jsonschema.validate(instance=order_json, schema=schema)


def test_position_schema_conformance():
    """Verify Position model JSON validates against position.schema.json."""
    schema = load_schema("position.schema.json")
    position = Position(
        positionId="POS-1001",
        symbol="XAUUSD",
        side=PositionSide.BUY,
        volume=1.0,
        entryPrice=2650.25,
        currentPrice=2652.00,
        stopLoss=2640.25,
        takeProfit=2670.25,
        unrealizedPnl=175.0,
        lifecycleId="00000000-0000-0000-0000-000000000002",
    )
    pos_json = position.model_dump(mode="json")
    jsonschema.validate(instance=pos_json, schema=schema)


def test_risk_decision_schema_conformance():
    """Verify RiskDecision model JSON validates against risk-decision.schema.json."""
    schema = load_schema("risk-decision.schema.json")
    decision = RiskDecision(
        decision=DecisionType.APPROVED,
        reasonCodes=["RISK_CHECKS_PASSED"],
        riskPercent=1.0,
        approvedVolume=1.0,
        tradeLifecycleId="00000000-0000-0000-0000-000000000003",
    )
    decision_json = decision.model_dump(mode="json")
    jsonschema.validate(instance=decision_json, schema=schema)
