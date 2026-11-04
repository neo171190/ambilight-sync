"""Tests for per-light command data (upstream capabilities + fork Kelvin output)."""

from types import SimpleNamespace

from custom_components.ambilight_sync.capabilities import command_data
from custom_components.ambilight_sync.light_output import kelvin_range, rgb_to_kelvin


def light(modes, **attributes):
    return SimpleNamespace(
        state="on",
        attributes={"supported_color_modes": modes, **attributes},
    )


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


def test_color_light_gets_rgb():
    data = command_data("light.a", light(["xy", "color_temp"]), (255, 0, 0), 100, 0)
    assert data == {"entity_id": "light.a", "rgb_color": (255, 0, 0), "brightness": 100}


def test_white_ambiance_light_gets_color_temperature():
    state = light(["color_temp"], min_color_temp_kelvin=2202, max_color_temp_kelvin=5000)
    data = command_data("light.a", state, (255, 0, 0), 100, 0)
    assert data == {"entity_id": "light.a", "color_temp_kelvin": 2202, "brightness": 100}
    assert command_data("light.a", state, (0, 0, 255), 100, 0)["color_temp_kelvin"] == 5000


def test_dimmable_and_onoff_lights():
    assert command_data("light.a", light(["brightness"]), (255, 0, 0), 80, 0) == {
        "entity_id": "light.a",
        "brightness": 80,
    }
    assert command_data("light.a", light(["onoff"]), (255, 0, 0), 80, 0) == {
        "entity_id": "light.a"
    }
