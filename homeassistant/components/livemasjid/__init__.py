"""The Livemasjid integration."""
from __future__ import annotations

import logging
import threading

from livemasjid import Livemasjid

import homeassistant.components.media_player as mp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID
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
        self.hass: HomeAssistant = hass
        self.entry = entry
        self.client: Livemasjid = client
        self.thread = threading.Thread(target=self.retrieve_pushes)
        self.thread.daemon = True
        self.thread.start()
        self.active_stream = "idle"

    def on_push(self, topic, message, status):
        """Update the current data."""
        subscriptions = self.entry.options["subscriptions"]

        if topic not in subscriptions:
            return

        if message == "stopped":
            if self.active_stream == topic:
                self.active_stream = "idle"
            return

        primary_subscription = self.entry.options["primary_subscription"]

        if self.active_stream == primary_subscription:
            return
        alternate_devices = self.entry.options["alternate_devices"]
        media_player_entity = self.entry.options["primary_device"]
        devices = [media_player_entity] + alternate_devices

        for device in devices:
            self.hass.services.call(
                mp.DOMAIN,
                mp.SERVICE_PLAY_MEDIA,
                {
                    ATTR_ENTITY_ID: device,
                    mp.ATTR_MEDIA_CONTENT_ID: status["stream_url"]
                    if status["stream_url"]
                    else f"https://relay.livemasjid.com:8443/{topic}",
                    mp.ATTR_MEDIA_CONTENT_TYPE: status["stream_type"]
                    if status["stream_type"]
                    else "audio/opus",
                },
            )

    def retrieve_pushes(self):
        """Retrieve_pushes.

        Spawn a new Listener and links it to self.on_push.
        """
        self.client.register_on_message_callback(self.on_push)
        self.client.start()


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
    lm: Livemasjid = hass.data[DOMAIN][entry.entry_id].get("client")
    lm.client.loop_stop(force=True)

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
