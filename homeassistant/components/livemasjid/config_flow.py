"""Config flow for Livemasjid integration."""
from __future__ import annotations

import logging

from livemasjid import Livemasjid
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant as hass, callback
from homeassistant.helpers import entity_registry

from .const import DEFAULT_SUBSCRIPTIONS, DOMAIN, ENTITIES, NAME, SUBSCRIPTIONS

_LOGGER = logging.getLogger(__name__)

# TODO adjust the data schema to the data that you need
STEP_USER_DATA_SCHEMA = vol.Schema(
    {vol.Optional("subscriptions"): str, vol.Optional("entities"): str}
)


class LivemasjidFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Livemasjid."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return LivemasjidOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is None:
            return self.async_show_form(step_id="user")

        return self.async_create_entry(title=NAME, data=user_input)

    async def async_step_import(self, import_config):
        """Import from config."""
        return await self.async_step_user(user_input=import_config)


class LivemasjidOptionsFlowHandler(hass, config_entries.OptionsFlow):
    """Handle Islamic Prayer client options."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        super().__init__()
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        lm = await self.async_add_executor_job(Livemasjid)
        subscriptions = lm.get_status()

        registry = await entity_registry.async_get_registry(self.hass)

        options = {
            vol.Optional(
                SUBSCRIPTIONS,
                default=self.config_entry.options.get(
                    SUBSCRIPTIONS, DEFAULT_SUBSCRIPTIONS
                ),
            ): vol.In(subscriptions.keys()),
            vol.Optional(
                ENTITIES,
                default=self.config_entry.options.get(ENTITIES, []),
            ): vol.In(
                [
                    value.entity_id
                    for key, value in registry.entities.items()
                    if "media_player." in value.entity_id
                ]
            ),
        }

        return self.async_show_form(step_id="init", data_schema=vol.Schema(options))
