"""Quick-feed button for Cat Feeding Tracker."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_DEFAULT_PORTION, DEFAULT_PORTION_G, DOMAIN
from .store import FeedingStore


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    store: FeedingStore = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([QuickFeedButton(entry, store)])


class QuickFeedButton(ButtonEntity):
    """Logs one default-size portion. Usable from the dashboard or Assist."""

    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_translation_key = "feed_now"
    _attr_icon = "mdi:food-drumstick-outline"

    def __init__(self, entry: ConfigEntry, store: FeedingStore) -> None:
        self._entry = entry
        self._store = store
        self._attr_unique_id = f"{entry.entry_id}_feed_now"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Cat Feeding Tracker",
            model="Katze",
        )

    async def async_press(self) -> None:
        amount = self._entry.options.get(CONF_DEFAULT_PORTION, DEFAULT_PORTION_G)
        await self._store.async_log_feeding(amount_g=amount, note="Quick-Feed Button")
