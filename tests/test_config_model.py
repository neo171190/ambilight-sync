"""Tests for configuration defaults and normalization."""

from custom_components.ambilight_sync.config_model import normalize_settings
from custom_components.ambilight_sync.const import (
    CONF_POLL_RATE,
    CONF_THRESHOLD,
    CONF_TRANSITION,
    CONF_UPDATE_RATE,
)


def test_new_presets_use_conservative_rates():
    settings = normalize_settings({})
    assert settings[CONF_POLL_RATE] == 4.0
    assert settings[CONF_UPDATE_RATE] == 3.0
    assert settings[CONF_TRANSITION] == 0.5
    assert settings[CONF_THRESHOLD] == 12.0


def test_stored_values_are_kept():
    settings = normalize_settings({CONF_POLL_RATE: 15, CONF_UPDATE_RATE: 15})
    assert settings[CONF_POLL_RATE] == 15.0
    assert settings[CONF_UPDATE_RATE] == 15.0


def test_legacy_update_rate_drives_poll_rate():
    settings = normalize_settings({CONF_UPDATE_RATE: 8})
    assert settings[CONF_POLL_RATE] == 8.0


def test_rates_are_clamped():
    settings = normalize_settings({CONF_POLL_RATE: 500, CONF_UPDATE_RATE: 0})
    assert settings[CONF_POLL_RATE] == 30.0
    assert settings[CONF_UPDATE_RATE] == 0.25
