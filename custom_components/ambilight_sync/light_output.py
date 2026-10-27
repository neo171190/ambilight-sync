"""Translate Ambilight output into service data a given light can apply.

Upstream always sent ``rgb_color``. Lights that only support white light
(color temperature, brightness) or plain on/off then depend on Home
Assistant's implicit conversion. Here every light gets data matched to its
own supported color modes instead.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

RGB = tuple[int, int, int]

CAPABILITY_COLOR = "color"
CAPABILITY_COLOR_TEMP = "color_temp"
CAPABILITY_BRIGHTNESS = "brightness"
CAPABILITY_ONOFF = "onoff"

_COLOR_MODES = {"hs", "xy", "rgb", "rgbw", "rgbww"}

DEFAULT_MIN_KELVIN = 2000
DEFAULT_MAX_KELVIN = 6500


def light_capability(supported_color_modes: Iterable[Any] | None) -> str:
    """Return the richest output a light supports.

    Unknown or missing information falls back to color, which is the
    upstream behavior.
    """
    modes = {str(mode) for mode in supported_color_modes or ()}
    if not modes or modes & _COLOR_MODES:
        return CAPABILITY_COLOR
    if "color_temp" in modes:
        return CAPABILITY_COLOR_TEMP
    if modes & {"brightness", "white"}:
        return CAPABILITY_BRIGHTNESS
    if "onoff" in modes:
        return CAPABILITY_ONOFF
    return CAPABILITY_COLOR


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
    This keeps the mood of a scene; a physically exact correlated color
    temperature is meaningless for saturated colors anyway.
    """
    red, blue = float(rgb[0]), float(rgb[2])
    if red + blue <= 0:
        return round((min_kelvin + max_kelvin) / 2)
    balance = (blue - red) / (red + blue)  # -1 (red) .. +1 (blue)
    return round(min_kelvin + (balance + 1.0) / 2.0 * (max_kelvin - min_kelvin))


def turn_on_data(
    capability: str,
    rgb: RGB,
    brightness: int,
    kelvin_bounds: tuple[int, int] = (DEFAULT_MIN_KELVIN, DEFAULT_MAX_KELVIN),
) -> dict[str, Any]:
    """Return light.turn_on data (without entity_id/transition) for a capability."""
    if capability == CAPABILITY_ONOFF:
        return {}
    if capability == CAPABILITY_BRIGHTNESS:
        return {"brightness": brightness}
    if capability == CAPABILITY_COLOR_TEMP:
        return {
            "color_temp_kelvin": rgb_to_kelvin(rgb, *kelvin_bounds),
            "brightness": brightness,
        }
    return {"rgb_color": rgb, "brightness": brightness}
