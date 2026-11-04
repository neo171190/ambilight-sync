"""Fork addition: color temperature output for white-ambiance lights.

Upstream sends lights without color support only a brightness. Lights that
support color temperature additionally get a white temperature that follows
the scene's red/blue balance: warm for red scenes, cool for blue scenes.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

RGB = tuple[int, int, int]

DEFAULT_MIN_KELVIN = 2000
DEFAULT_MAX_KELVIN = 6500


def kelvin_range(attributes: Mapping[str, Any]) -> tuple[int, int]:
    """Return the light's supported color temperature range in Kelvin."""
    try:
        low = int(attributes.get("min_color_temp_kelvin") or DEFAULT_MIN_KELVIN)
        high = int(attributes.get("max_color_temp_kelvin") or DEFAULT_MAX_KELVIN)
    except (TypeError, ValueError):
        return DEFAULT_MIN_KELVIN, DEFAULT_MAX_KELVIN
    if low > high:
        low, high = high, low
    return low, high


def rgb_to_kelvin(rgb: RGB, min_kelvin: int, max_kelvin: int) -> int:
    """Map a color to a white temperature by its red/blue balance.

    Red-dominant colors become the warmest supported white, blue-dominant
    colors the coolest, neutral and green colors the middle of the range.
    """
    red, blue = float(rgb[0]), float(rgb[2])
    if red + blue <= 0:
        return round((min_kelvin + max_kelvin) / 2)
    balance = (blue - red) / (red + blue)  # -1 (red) .. +1 (blue)
    return round(min_kelvin + (balance + 1.0) / 2.0 * (max_kelvin - min_kelvin))
