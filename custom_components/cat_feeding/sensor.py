"""Sensors for Cat Feeding Tracker."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_DAILY_TARGET, DOMAIN, SIGNAL_UPDATE
from .store import FeedingStore


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    store: FeedingStore = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            TodayTotalSensor(entry, store),
            TodayCountSensor(entry, store),
            LastFeedingTimeSensor(entry, store),
            LastFeedingAmountSensor(entry, store),
            WeeklyAverageSensor(entry, store),
            DailyTargetRemainingSensor(entry, store),
        ]
    )


class _BaseFeedingSensor(SensorEntity):
    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry, store: FeedingStore) -> None:
        self._entry = entry
        self._store = store
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Cat Feeding Tracker",
            model="Katze",
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_UPDATE.format(entry_id=self._entry.entry_id),
                self._handle_update,
            )
        )

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()


class TodayTotalSensor(_BaseFeedingSensor):
    _attr_translation_key = "today_total"
    _attr_native_unit_of_measurement = "g"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:food-drumstick"

    def __init__(self, entry: ConfigEntry, store: FeedingStore) -> None:
        super().__init__(entry, store)
        self._attr_unique_id = f"{entry.entry_id}_today_total"

    @property
    def native_value(self) -> float:
        return self._store.today_total_g


class TodayCountSensor(_BaseFeedingSensor):
    _attr_translation_key = "today_count"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:counter"

    def __init__(self, entry: ConfigEntry, store: FeedingStore) -> None:
        super().__init__(entry, store)
        self._attr_unique_id = f"{entry.entry_id}_today_count"

    @property
    def native_value(self) -> int:
        return self._store.today_count


class LastFeedingTimeSensor(_BaseFeedingSensor):
    _attr_translation_key = "last_feeding_time"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-outline"

    def __init__(self, entry: ConfigEntry, store: FeedingStore) -> None:
        super().__init__(entry, store)
        self._attr_unique_id = f"{entry.entry_id}_last_feeding_time"

    @property
    def native_value(self):
        last = self._store.last_event
        return last.timestamp if last else None

    @property
    def extra_state_attributes(self) -> dict:
        last = self._store.last_event
        if not last:
            return {}
        return {"food_type": last.food_type, "note": last.note}


class LastFeedingAmountSensor(_BaseFeedingSensor):
    _attr_translation_key = "last_feeding_amount"
    _attr_native_unit_of_measurement = "g"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:scale"

    def __init__(self, entry: ConfigEntry, store: FeedingStore) -> None:
        super().__init__(entry, store)
        self._attr_unique_id = f"{entry.entry_id}_last_feeding_amount"

    @property
    def native_value(self) -> float | None:
        last = self._store.last_event
        return last.amount_g if last else None


class WeeklyAverageSensor(_BaseFeedingSensor):
    _attr_translation_key = "weekly_average"
    _attr_native_unit_of_measurement = "g"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:chart-line"

    def __init__(self, entry: ConfigEntry, store: FeedingStore) -> None:
        super().__init__(entry, store)
        self._attr_unique_id = f"{entry.entry_id}_weekly_average"

    @property
    def native_value(self) -> float:
        return self._store.average_daily_total_g(days=7)


class DailyTargetRemainingSensor(_BaseFeedingSensor):
    _attr_translation_key = "daily_target_remaining"
    _attr_native_unit_of_measurement = "g"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:target"

    def __init__(self, entry: ConfigEntry, store: FeedingStore) -> None:
        super().__init__(entry, store)
        self._attr_unique_id = f"{entry.entry_id}_daily_target_remaining"

    @property
    def native_value(self) -> float:
        target = self._entry.options.get(CONF_DAILY_TARGET, 0)
        return round(max(target - self._store.today_total_g, 0), 1)
