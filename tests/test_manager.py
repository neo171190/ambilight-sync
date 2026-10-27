"""Behavior tests for the sync manager with a simulated Philips TV."""

from __future__ import annotations

import asyncio

from haphilipsjs import ConnectionFailure
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_service,
)

from custom_components.ambilight_sync import manager as manager_module
from custom_components.ambilight_sync.const import DOMAIN
from custom_components.ambilight_sync.manager import AmbilightSyncManager

COLOR = "light.color"
WHITE = "light.white"
ONOFF = "light.onoff"


def ambilight_payload(rgb: tuple[int, int, int]) -> dict:
    pixel = {"r": rgb[0], "g": rgb[1], "b": rgb[2]}
    side = {str(index): dict(pixel) for index in range(4)}
    return {"layer1": {"left": dict(side), "right": dict(side), "top": dict(side)}}


class FakeTV:
    """Stands in for haphilipsjs.PhilipsTV."""

    def __init__(self) -> None:
        self.payload: dict | None = ambilight_payload((255, 0, 0))
        self.reachable = True
        self.power = "On"
        self.power_checks = 0

        class _Session:
            async def aclose(self) -> None:
                return None

        self.session = _Session()

    async def getAmbilightProcessed(self):
        if not self.reachable:
            raise ConnectionFailure("TV unreachable")
        return self.payload

    getAmbilightMeasured = getAmbilightProcessed

    async def getPowerState(self):
        self.power_checks += 1
        if not self.reachable:
            raise ConnectionFailure("TV unreachable")
        return {"powerstate": self.power}


def profile(lights: list[str]) -> dict:
    return {
        "active_preset": "default",
        "presets": {
            "default": {
                "name": "Default",
                "global": {
                    "poll_rate": 20,
                    "update_rate": 20,
                    "transition": 0,
                    "threshold": 0,
                    "scene_cut_threshold": 0,
                },
                "lights": {
                    entity_id: {"sources": [{"zone": "all", "weight": 100}]}
                    for entity_id in lights
                },
            }
        },
    }


@pytest.fixture
def fast_timing(monkeypatch):
    monkeypatch.setattr(manager_module, "TV_RELEASE_SECONDS", 0.3)
    monkeypatch.setattr(manager_module, "TV_IDLE_POLL_SECONDS", 0.05)
    monkeypatch.setattr(manager_module, "TV_POWER_CHECK_SECONDS", 0.05)
    monkeypatch.setattr(manager_module, "TV_ZERO_BEFORE_POWER_CHECK", 0.05)


@pytest.fixture
async def setup(hass, fast_timing):
    """Create lights, recorded light services and a manager with a fake TV."""
    hass.states.async_set(
        COLOR,
        "on",
        {
            "supported_color_modes": ["xy", "color_temp"],
            "rgb_color": [0, 0, 255],
            "brightness": 100,
        },
    )
    hass.states.async_set(
        WHITE,
        "off",
        {
            "supported_color_modes": ["color_temp"],
            "min_color_temp_kelvin": 2202,
            "max_color_temp_kelvin": 5000,
        },
    )
    hass.states.async_set(ONOFF, "off", {"supported_color_modes": ["onoff"]})
    turn_on = async_mock_service(hass, "light", "turn_on")
    turn_off = async_mock_service(hass, "light", "turn_off")

    entry = MockConfigEntry(domain=DOMAIN, data={"host": "192.0.2.1", "api_version": 6})
    entry.add_to_hass(hass)
    manager = AmbilightSyncManager(
        hass,
        entry=entry,
        host="192.0.2.1",
        api_version=6,
        system={},
        username=None,
        password=None,
        profile_config=profile([COLOR, WHITE, ONOFF]),
    )
    tv = FakeTV()
    manager.tv = tv
    yield manager, tv, turn_on, turn_off
    await manager.async_stop(restore=False)


def calls_for(calls, entity_id):
    return [call.data for call in calls if call.data.get("entity_id") == entity_id]


async def test_each_light_gets_data_it_can_show(hass, setup):
    manager, _tv, turn_on, _turn_off = setup
    await manager.async_start()
    await asyncio.sleep(0.2)

    color = calls_for(turn_on, COLOR)
    white = calls_for(turn_on, WHITE)
    onoff = calls_for(turn_on, ONOFF)
    assert color and color[-1]["rgb_color"] == (255, 0, 0)
    assert white and "rgb_color" not in white[-1]
    assert white[-1]["color_temp_kelvin"] == 2202  # red -> warmest white
    assert onoff and set(onoff[-1]) == {"entity_id"}


async def test_white_light_is_not_flooded_by_unchanged_frames(hass, setup):
    manager, _tv, turn_on, _turn_off = setup
    await manager.async_start()
    await asyncio.sleep(0.5)
    # Same TV color for ~10 polls: one command per light, not one per frame.
    assert len(calls_for(turn_on, WHITE)) == 1
    assert len(calls_for(turn_on, ONOFF)) == 1


async def test_unreachable_tv_releases_and_restores_lights(hass, setup):
    manager, tv, turn_on, turn_off = setup
    await manager.async_start()
    await asyncio.sleep(0.15)
    turn_on.clear()
    turn_off.clear()

    tv.reachable = False
    await asyncio.sleep(0.6)

    assert manager.waiting_for_tv
    assert manager.is_running
    restored = calls_for(turn_on, COLOR)
    assert restored and restored[-1]["rgb_color"] == [0, 0, 255]
    assert restored[-1]["brightness"] == 100
    assert calls_for(turn_off, WHITE)
    assert calls_for(turn_off, ONOFF)


async def test_sync_resumes_when_tv_returns(hass, setup):
    manager, tv, turn_on, _turn_off = setup
    await manager.async_start()
    tv.reachable = False
    await asyncio.sleep(0.6)
    assert manager.waiting_for_tv
    turn_on.clear()

    tv.reachable = True
    tv.payload = ambilight_payload((0, 255, 0))
    await asyncio.sleep(0.3)

    assert not manager.waiting_for_tv
    color = calls_for(turn_on, COLOR)
    assert color and color[-1]["rgb_color"] == (0, 255, 0)


async def test_standby_tv_releases_lights(hass, setup):
    manager, tv, turn_on, _turn_off = setup
    await manager.async_start()
    await asyncio.sleep(0.15)
    turn_on.clear()

    tv.payload = ambilight_payload((0, 0, 0))
    tv.power = "Standby"
    await asyncio.sleep(0.8)

    assert manager.waiting_for_tv
    assert tv.power_checks >= 1
    restored = calls_for(turn_on, COLOR)
    assert restored and restored[-1]["rgb_color"] == [0, 0, 255]


async def test_dark_scene_with_tv_on_keeps_sync_active(hass, setup):
    manager, tv, _turn_on, _turn_off = setup
    await manager.async_start()
    await asyncio.sleep(0.15)

    tv.payload = ambilight_payload((0, 0, 0))
    tv.power = "On"
    await asyncio.sleep(0.8)

    assert not manager.waiting_for_tv
    assert tv.power_checks >= 1


async def test_stop_after_release_does_not_restore_again(hass, setup):
    manager, tv, turn_on, turn_off = setup
    await manager.async_start()
    tv.reachable = False
    await asyncio.sleep(0.6)
    assert manager.waiting_for_tv

    # The user switches the lights by hand while the TV is off ...
    turn_on.clear()
    turn_off.clear()
    # ... and an automation stops the sync afterwards.
    await manager.async_stop()

    assert not turn_on
    assert not turn_off
    assert not manager.waiting_for_tv
