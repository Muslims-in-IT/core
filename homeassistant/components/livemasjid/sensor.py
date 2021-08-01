"""Platform to retrieve Livemasjid information for Home Assistant."""
import logging
from typing import Final

from livemasjid import Livemasjid

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import (
    DATA_UPDATED,
    DOMAIN,
    LIVEMASJID_ACTIVE_STREAM,
    LIVEMASJID_SENSOR_ICON,
)

_LOGGER: Final = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Livemasjid sensor platform."""
    subscriptions = config_entry.options.get("subscriptions", [])
    domain_data = hass.data[DOMAIN][config_entry.entry_id]
    client: Livemasjid = domain_data["client"]
    client.set_subscriptions(subscriptions)
    status = client.get_status()
    entities = []

    for sensor_type in status:
        if sensor_type not in subscriptions:
            continue
        entities.append(LivemasjidSensor(sensor_type, client))

    entities.append(LivemasjidActiveStreamSensor(LIVEMASJID_ACTIVE_STREAM))

    async_add_entities(entities, True)


class LivemasjidSensor(SensorEntity):
    """Representation of a Livemasjid sensor."""

    _attr_icon = LIVEMASJID_SENSOR_ICON
    _attr_should_poll = False

    def __init__(self, sensor_type, client):
        """Initialize the Livemasjid sensor."""
        self.sensor_type = sensor_type
        self.client = client
        self._attributes = None

    @property
    def name(self):
        """Return the name of the sensor."""
        status = self.client.get_status()
        return status[self.sensor_type]["name"]

    @property
    def unique_id(self):
        """Return the unique id of the entity."""
        return self.sensor_type

    @property
    def state(self):
        """Return the state of the sensor."""
        return (
            self.client.get_status().get(self.sensor_type, {}).get("status", "offline")
        )

    @property
    def extra_state_attributes(self):
        """State attributes."""
        self._attributes = self.client.get_status().get(self.sensor_type, {})
        return self._attributes

    async def async_added_to_hass(self):
        """Handle entity which will be added."""
        self.async_on_remove(
            async_dispatcher_connect(self.hass, DATA_UPDATED, self.async_write_ha_state)
        )

    # def update(self):
    #     self.async_schedule_update_ha_state()


class LivemasjidActiveStreamSensor(SensorEntity):
    """Representation of an Livemasjid sensor."""

    _attr_icon = LIVEMASJID_SENSOR_ICON
    _attr_should_poll = False

    def __init__(self, sensor_type):
        """Initialize the Livemasjid sensor."""
        self.sensor_type = sensor_type
        self._attributes = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Livemasjid Active Stream"

    @property
    def unique_id(self):
        """Return the unique id of the entity."""
        return self.sensor_type

    @property
    def state(self):
        """Return the state of the sensor."""
        return "idle"

    async def async_added_to_hass(self):
        """Handle entity which will be added."""
        self.async_on_remove(
            async_dispatcher_connect(self.hass, DATA_UPDATED, self.async_write_ha_state)
        )
