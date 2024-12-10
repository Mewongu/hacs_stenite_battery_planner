# custom_components/stenite_battery_planner/sensor.py
from __future__ import annotations

import logging
from typing import Any, Dict
from datetime import datetime

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfPower,
    UnitOfTime,
)

from . import DOMAIN, BatteryPlannerCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        async_add_entities: AddEntitiesCallback,
        discovery_info: DiscoveryInfoType | None = None
):
    """Set up the Battery Planner sensor platform."""
    coordinator = hass.data.get(DOMAIN)

    if coordinator is None:
        _LOGGER.error("No Battery Planner coordinator found")
        return

    entities = [
        BatteryPlannerPowerSensor(coordinator),
        BatteryPlannerStatusSensor(coordinator),
        BatteryPlannerSearchTimeSensor(coordinator),
        BatteryPlannerScheduleSensor(coordinator),
    ]

    async_add_entities(entities)


class BatteryPlannerPowerSensor(CoordinatorEntity, SensorEntity):
    """Current power recommendation from planner."""

    def __init__(self, coordinator: BatteryPlannerCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_power"
        self._attr_name = "Battery Planner Power"
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float | None:
        """Return the power value."""
        return self.coordinator.data.get('watts')


class BatteryPlannerStatusSensor(CoordinatorEntity, SensorEntity):
    """Status of the optimization."""

    def __init__(self, coordinator: BatteryPlannerCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_status"
        self._attr_name = "Battery Planner Status"

    @property
    def native_value(self) -> str | None:
        """Return the status."""
        return self.coordinator.data.get('status')


class BatteryPlannerSearchTimeSensor(CoordinatorEntity, SensorEntity):
    """Time spent searching for optimization."""

    def __init__(self, coordinator: BatteryPlannerCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_search_time"
        self._attr_name = "Battery Planner Search Time"
        self._attr_native_unit_of_measurement = UnitOfTime.SECONDS
        self._attr_device_class = SensorDeviceClass.DURATION
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float | None:
        """Return the search time."""
        return self.coordinator.data.get('search_time')


class BatteryPlannerScheduleSensor(CoordinatorEntity, SensorEntity):
    """Schedule of planned battery operations."""

    def __init__(self, coordinator: BatteryPlannerCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_schedule"
        self._attr_name = "Battery Planner Schedule"

    @property
    def native_value(self) -> str | None:
        """Return current/next schedule entry."""
        schedule = self.coordinator.data.get('schedule', [])
        if not schedule:
            return None

        # Find the current/next applicable schedule entry
        now = datetime.now()
        current_entry = None

        for entry in schedule:
            entry_time = datetime.fromisoformat(entry['time'])
            if entry_time >= now:
                current_entry = entry
                break

        if current_entry:
            return f"{current_entry['watts']}W at {current_entry['time']} (Price: {current_entry['price']})"
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the full schedule."""
        return {'schedule': self.coordinator.data.get('schedule', [])}