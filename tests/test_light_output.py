"""Tests for per-light output translation."""

from custom_components.ambilight_sync.light_output import (
    CAPABILITY_BRIGHTNESS,
    CAPABILITY_COLOR,
    CAPABILITY_COLOR_TEMP,
    CAPABILITY_ONOFF,
    kelvin_range,
    light_capability,
    rgb_to_kelvin,
    turn_on_data,
)


def test_capability_prefers_color():
    assert light_capability(["color_temp", "xy"]) == CAPABILITY_COLOR
    assert light_capability(["rgbww"]) == CAPABILITY_COLOR


def test_capability_white_only_lights():
    assert light_capability(["color_temp"]) == CAPABILITY_COLOR_TEMP
    assert light_capability(["brightness"]) == CAPABILITY_BRIGHTNESS
    assert light_capability(["onoff"]) == CAPABILITY_ONOFF


def test_capability_unknown_falls_back_to_color():
    assert light_capability(None) == CAPABILITY_COLOR
    assert light_capability([]) == CAPABILITY_COLOR


def test_kelvin_mapping_follows_red_blue_balance():
    low, high = 2202, 5000
    assert rgb_to_kelvin((255, 0, 0), low, high) == low
    assert rgb_to_kelvin((0, 0, 255), low, high) == high
    neutral = rgb_to_kelvin((255, 255, 255), low, high)
    assert neutral == round((low + high) / 2)
    assert rgb_to_kelvin((0, 255, 0), low, high) == neutral
    assert low < rgb_to_kelvin((255, 160, 60), low, high) < neutral


def test_kelvin_range_handles_missing_and_swapped_values():
    assert kelvin_range({}) == (2000, 6500)
    assert kelvin_range({"min_color_temp_kelvin": 5000, "max_color_temp_kelvin": 2202}) == (2202, 5000)
    assert kelvin_range({"min_color_temp_kelvin": "x"}) == (2000, 6500)


def test_turn_on_data_per_capability():
    rgb = (255, 0, 0)
    assert turn_on_data(CAPABILITY_COLOR, rgb, 100) == {"rgb_color": rgb, "brightness": 100}
    assert turn_on_data(CAPABILITY_COLOR_TEMP, rgb, 100, (2202, 5000)) == {
        "color_temp_kelvin": 2202,
        "brightness": 100,
    }
    assert turn_on_data(CAPABILITY_BRIGHTNESS, rgb, 100) == {"brightness": 100}
    assert turn_on_data(CAPABILITY_ONOFF, rgb, 100) == {}
