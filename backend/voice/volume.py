"""
Volume conversion utilities for Discord RPC

Discord RPC stores AMPLITUDE, but Discord UI displays PERCEPTUAL values.
Calculated empirically: amplitude=5 → UI shows 31% → range ≈ 38dB
For boost (>100%), we use 6dB as in the official library.
"""

import math
from typing import Union

DEFAULT_VOLUME_DYNAMIC_RANGE_DB = 38  # Empirically calculated
DEFAULT_VOLUME_BOOST_DYNAMIC_RANGE_DB = 6


def perceptual_to_amplitude(perceptual: float, max_value: float = 100) -> float:
    """
    Convert perceptual volume (what the user sees) to amplitude (what Discord RPC expects).

    Args:
        perceptual: User-facing volume value (0-100 for input, 0-200 for output)
        max_value: Maximum allowed value (100 for input, 200 for output)

    Returns:
        Amplitude value to send to Discord RPC

    Example:
        >>> perceptual_to_amplitude(50, 100)  # 50% input volume
        31.622776601683793
    """
    if perceptual <= 0:
        return 0.0
    if perceptual >= max_value:
        return float(max_value)

    # For output volume (max_value=200), 100% is normal, 100-200% is boost
    normalized_max = 100.0 if max_value > 100 else float(max_value)

    if perceptual > normalized_max:
        # Boost range: for values above 100%
        db = ((perceptual - normalized_max) / normalized_max) * DEFAULT_VOLUME_BOOST_DYNAMIC_RANGE_DB
    else:
        # Normal range: 0-100%
        db = (perceptual / normalized_max) * DEFAULT_VOLUME_DYNAMIC_RANGE_DB - DEFAULT_VOLUME_DYNAMIC_RANGE_DB

    amplitude = normalized_max * (10 ** (db / 20))
    return max(0.0, min(float(max_value), amplitude))


def amplitude_to_perceptual(amplitude: float, max_value: float = 100) -> float:
    """
    Convert amplitude (what Discord RPC returns) to perceptual (what the user sees).

    Args:
        amplitude: Amplitude value from Discord RPC
        max_value: Maximum allowed value (100 for input, 200 for output)

    Returns:
        Perceptual volume value for display

    Example:
        >>> amplitude_to_perceptual(31.62, 100)  # ~50% perceptual
        50.0
    """
    if amplitude <= 0:
        return 0.0
    if amplitude >= max_value:
        return float(max_value)

    # For output volume (max_value=200), normalized_max is 100
    normalized_max = 100.0 if max_value > 100 else float(max_value)

    db = 20 * math.log10(amplitude / normalized_max)

    if db > 0:
        # Boost range: amplitude above 100%
        perceptual = (db / DEFAULT_VOLUME_BOOST_DYNAMIC_RANGE_DB + 1) * normalized_max
    else:
        # Normal range
        perceptual = (DEFAULT_VOLUME_DYNAMIC_RANGE_DB + db) / DEFAULT_VOLUME_DYNAMIC_RANGE_DB * normalized_max

    return max(0.0, min(float(max_value), perceptual))
