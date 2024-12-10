# custom_components/stenite_battery_planner/sensor.py
from __future__ import annotations

import logging
from typing import Any, Dict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass

from . import DOMAIN, BatteryPlannerCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        async_add_entities: AddEntitiesCallback,
        discovery_info: DiscoveryInfoType | None = None
):
    """Set up the Battery Planner sensor platform."""
    # Find the coordinator
    coordinator = hass.data.get(DOMAIN)

    if coordinator is None:
        _LOGGER.error("No Battery Planner coordinator found")
        return

    async_add_entities([
        BatteryPlanSensor(coordinator, 'watts'),
        BatteryPlanSensor(coordinator, 'status'),
        BatteryPlanSensor(coordinator, 'search_time'),
        BatteryPlanSensor(coordinator, 'schedule'),
    ])


class BatteryPlanSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Battery Planner Sensor."""

    def __init__(self, coordinator: BatteryPlannerCoordinator, attribute):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_sensor_{attribute}"
        self._attr_name = f"Battery Plan {attribute}"
        self._attribute = attribute

    @property
    def state(self) -> str:
        """Return the state of the sensor."""
        # Default to 'Unknown' if no data
        return self.coordinator.data.get(self._attribute, 'Unknown')

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the full response as attributes."""
        return self.coordinator.data or {}