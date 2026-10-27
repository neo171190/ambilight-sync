"""The integration loads from custom_components and exposes its switch."""

from unittest.mock import patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ambilight_sync.const import DOMAIN


async def test_setup_and_unload(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Ambilight Sync · Test TV",
        data={"host": "192.0.2.1", "api_version": 6, "system": {"name": "Test TV"}},
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.ambilight_sync.async_register_frontend",
        return_value=None,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    states = [s for s in hass.states.async_all("switch") if s.entity_id.startswith("switch.")]
    assert len(states) == 1
    assert states[0].state == "off"
    assert states[0].attributes["waiting_for_tv"] is False
    assert hass.services.has_service(DOMAIN, "activate_preset")

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
