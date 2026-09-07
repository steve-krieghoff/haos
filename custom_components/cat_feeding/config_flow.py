"""Config flow for Cat Feeding Tracker."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .const import (
    CONF_DAILY_TARGET,
    CONF_DEFAULT_PORTION,
    DEFAULT_DAILY_TARGET_G,
    DEFAULT_PORTION_G,
    DOMAIN,
)


def _user_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, "Katze")): str,
            vol.Required(
                CONF_DEFAULT_PORTION,
                default=defaults.get(CONF_DEFAULT_PORTION, DEFAULT_PORTION_G),
            ): NumberSelector(
                NumberSelectorConfig(min=1, max=1000, step=1, unit_of_measurement="g", mode=NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_DAILY_TARGET,
                default=defaults.get(CONF_DAILY_TARGET, DEFAULT_DAILY_TARGET_G),
            ): NumberSelector(
                NumberSelectorConfig(min=1, max=5000, step=1, unit_of_measurement="g", mode=NumberSelectorMode.BOX)
            ),
        }
    )


class CatFeedingConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Cat Feeding Tracker."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_NAME].strip().lower())
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input[CONF_NAME], data={}, options=user_input
            )

        return self.async_show_form(
            step_id="user", data_schema=_user_schema(), errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> "CatFeedingOptionsFlow":
        return CatFeedingOptionsFlow(config_entry)


class CatFeedingOptionsFlow(OptionsFlow):
    """Handle options (default portion / daily target) for an existing cat."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current = dict(self._config_entry.options)
        current.setdefault(CONF_NAME, self._config_entry.title)
        schema = _user_schema(current)
        # Name is fixed after creation; drop it from the options form.
        schema = vol.Schema(
            {k: v for k, v in schema.schema.items() if k != CONF_NAME}
        )
        return self.async_show_form(step_id="init", data_schema=schema)
