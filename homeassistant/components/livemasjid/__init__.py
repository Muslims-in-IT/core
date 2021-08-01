"""The Livemasjid integration."""
from __future__ import annotations

import logging
import threading

from livemasjid import Livemasjid

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS = ["sensor"]


class LivemasjidUpdateListener:
    """Representation of a Livemasjid Listener."""

    def __init__(self, client, hass, entry):
        """Initialize the livemasjid listener."""
        self.hass = hass
        self.entry = entry
        self.client: Livemasjid = client
        self.thread = threading.Thread(target=self.retrieve_pushes)
        self.thread.daemon = True
        self.thread.start()

    def on_push(self, topic, message, status):
        """Update the current data."""
        _LOGGER.warning(
            f"Received message for topic: {topic}: {message}, state: {status}"
        )
        subscriptions = self.entry.options["subscriptions"]
        if topic not in subscriptions:
            return

        # registry_entities = await entity_registry.async_get_registry(self.hass)
        # entity_to_update = registry_entities.async_get(f"sensor.{topic}")
        # _LOGGER.warning(entity_to_update)

    def retrieve_pushes(self):
        """Retrieve_pushes.

        Spawn a new Listener and links it to self.on_push.
        """
        self.client.register_on_message_callback(self.on_push)

        try:
            self.client.start()
        finally:
            self.client.register_on_message_callback(None)
            _LOGGER.info(
                "We need to kill the client, but the API does not provide for this currently"
            )


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Livemasjid from a config entry."""
    _LOGGER.info(hass)
    _LOGGER.info(entry)
    _LOGGER.warning("Setting up client")
    subscriptions = entry.options.get("subscriptions", [])
    client: Livemasjid = await hass.async_add_executor_job(Livemasjid, subscriptions)
    hass.data.setdefault(DOMAIN, {})
    listener = LivemasjidUpdateListener(client, hass, entry=entry)
    hass.data[DOMAIN][entry.entry_id] = {"client": client, "listener": listener}
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
