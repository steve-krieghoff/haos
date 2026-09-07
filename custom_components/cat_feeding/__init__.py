"""The Cat Feeding Tracker integration."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv, device_registry as dr
from homeassistant.helpers.event import async_track_time_change

from .const import ATTR_AMOUNT, ATTR_FOOD_TYPE, ATTR_NOTE, DOMAIN, SERVICE_LOG_FEEDING
from .store import FeedingStore

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON]

LOG_FEEDING_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_AMOUNT): vol.All(vol.Coerce(float), vol.Range(min=0.1)),
        vol.Optional(ATTR_FOOD_TYPE): cv.string,
        vol.Optional(ATTR_NOTE): cv.string,
        vol.Optional("device_id"): cv.string,
        vol.Optional("config_entry_id"): cv.string,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Cat Feeding Tracker from a config entry."""
    store = FeedingStore(hass, entry.entry_id)
    await store.async_load()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = store

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    # Force sensors to recompute at local midnight so "today" totals reset
    # even if no feeding is logged right at rollover.
    entry.async_on_unload(
        async_track_time_change(
            hass,
            lambda _now: store.notify_update(),
            hour=0,
            minute=0,
            second=1,
        )
    )

    _async_register_service(hass)

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_LOG_FEEDING)
    return unload_ok


def _async_register_service(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_LOG_FEEDING):
        return

    async def _handle_log_feeding(call: ServiceCall) -> None:
        entries: dict = hass.data.get(DOMAIN, {})
        if not entries:
            raise HomeAssistantError("Keine Katze konfiguriert (cat_feeding).")

        entry_id = call.data.get("config_entry_id")

        if not entry_id and call.data.get("device_id"):
            device_registry = dr.async_get(hass)
            device = device_registry.async_get(call.data["device_id"])
            if device:
                for config_entry_id in device.config_entries:
                    if config_entry_id in entries:
                        entry_id = config_entry_id
                        break

        if not entry_id:
            if len(entries) == 1:
                entry_id = next(iter(entries))
            else:
                raise HomeAssistantError(
                    "Mehrere Katzen konfiguriert - bitte device_id oder "
                    "config_entry_id angeben."
                )

        store: FeedingStore | None = entries.get(entry_id)
        if store is None:
            raise HomeAssistantError(f"Unbekannter Eintrag: {entry_id}")

        await store.async_log_feeding(
            amount_g=call.data[ATTR_AMOUNT],
            food_type=call.data.get(ATTR_FOOD_TYPE),
            note=call.data.get(ATTR_NOTE),
        )

    hass.services.async_register(
        DOMAIN, SERVICE_LOG_FEEDING, _handle_log_feeding, schema=LOG_FEEDING_SCHEMA
    )
