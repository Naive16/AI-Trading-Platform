"""Deterministic position sizing calculations using instrument abstractions."""
import math

from ..models.market import InstrumentSpec


class PositionSizer:
    """Calculates risk-based position sizing without hard-coded broker constants."""

    @staticmethod
    def calculate_volume(
        equity: float,
        risk_percent: float,
        entry: float,
        stop_loss: float,
        instrument: InstrumentSpec,
    ) -> tuple[float, float]:
        """
        Calculate executable volume based on risk percentage and stop-loss distance.

        Returns:
            Tuple[float, float]: (rounded_volume, actual_risk_amount)
        """
        if equity <= 0:
            return 0.0, 0.0

        if entry <= 0 or stop_loss <= 0:
            return 0.0, 0.0

        sl_distance = abs(entry - stop_loss)
        if sl_distance <= 1e-6:
            return 0.0, 0.0

        # Normalize risk percentage: 0.5 means 0.5% of equity (0.005)
        # If risk_percent > 1.0 (e.g. 2.0 = 2%), divide by 100
        # If risk_percent <= 0.05, treat as fraction (e.g. 0.02 = 2%) or if given as 0.5% divide by 100.
        # Standard convention: riskPercent field is percent (e.g. 0.5 = 0.5%, 1.0 = 1.0%, 2.0 = 2.0%).
        risk_fraction = (risk_percent / 100.0) if risk_percent >= 0.1 else risk_percent
        risk_amount = equity * risk_fraction

        # Value per 1.0 lot price change = contractSize
        # Loss per 1.0 lot for stop-loss distance = sl_distance * contractSize
        loss_per_unit = sl_distance * instrument.contractSize
        if loss_per_unit <= 1e-9:
            return 0.0, 0.0

        raw_volume = risk_amount / loss_per_unit

        # Align with volumeStep (e.g. 0.01)
        step = instrument.volumeStep if instrument.volumeStep > 0 else 0.01
        steps = math.floor(raw_volume / step)
        volume = round(steps * step, 4)

        # Bounds check against instrument min/max
        if volume < instrument.minVolume:
            # Cannot safely size down without exceeding risk
            return 0.0, 0.0

        volume = min(volume, instrument.maxVolume)
        actual_risk = volume * loss_per_unit

        return volume, actual_risk
