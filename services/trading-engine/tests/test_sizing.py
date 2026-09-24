"""Tests for position sizing calculations."""
from services.trading_engine.app.models.market import InstrumentSpec
from services.trading_engine.app.risk.sizing import PositionSizer


def test_position_sizing_derivation():
    """Verify position sizing calculates appropriate volume from equity, risk, and SL distance."""
    spec = InstrumentSpec(symbol="XAUUSD", contractSize=100.0, minVolume=0.01, maxVolume=50.0, volumeStep=0.01)

    # 100,000 equity, 1% risk = $1,000 risk
    # entry 2650, stop 2640 => distance = 10.0
    # loss per 1.0 lot = 10.0 * 100 = $1,000
    # expected volume = 1,000 / 1,000 = 1.00 lot
    volume, risk_amount = PositionSizer.calculate_volume(
        equity=100000.0,
        risk_percent=1.0,
        entry=2650.0,
        stop_loss=2640.0,
        instrument=spec,
    )
    assert volume == 1.0
    assert risk_amount == 1000.0


def test_position_sizing_small_account():
    """Verify position sizing rounds down and adheres to minimum lot."""
    spec = InstrumentSpec(symbol="XAUUSD", contractSize=100.0, minVolume=0.01, maxVolume=50.0, volumeStep=0.01)

    # 5,000 equity, 0.5% risk = $25 risk
    # entry 2650, stop 2640 => distance = 10
    # loss per lot = 1000
    # raw volume = 25 / 1000 = 0.025 => step 0.01 => 0.02 lot
    volume, risk_amount = PositionSizer.calculate_volume(
        equity=5000.0,
        risk_percent=0.5,
        entry=2650.0,
        stop_loss=2640.0,
        instrument=spec,
    )
    assert volume == 0.02
    assert risk_amount == 20.0  # 0.02 * 1000


def test_position_sizing_below_minimum_lot():
    """Verify zero volume returned if risk budget cannot afford min volume."""
    spec = InstrumentSpec(symbol="XAUUSD", contractSize=100.0, minVolume=0.01, maxVolume=50.0, volumeStep=0.01)

    # 100 equity, 1% risk = $1 risk
    # entry 2650, stop 2640 => loss per lot = 1000
    # min lot 0.01 requires $10 risk > $1
    volume, risk_amount = PositionSizer.calculate_volume(
        equity=100.0,
        risk_percent=1.0,
        entry=2650.0,
        stop_loss=2640.0,
        instrument=spec,
    )
    assert volume == 0.0
    assert risk_amount == 0.0
