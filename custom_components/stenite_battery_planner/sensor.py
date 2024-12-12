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
        BatteryPlannerActionSensor(coordinator),
        BatteryPlannerSearchTimeSensor(coordinator),
        BatteryPlannerScheduleSensor(coordinator),
        BatteryPlannerScheduleInfoSensor(coordinator),
        BatteryPlannerEnergyCostSensor(coordinator),
        BatteryPlannerNetworkCostSensor(coordinator),
        BatteryPlannerCyclingCostSensor(coordinator),
        BatteryPlannerTotalCostSensor(coordinator),
        BatteryPlannerBaselineCostSensor(coordinator),
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


class BatteryPlannerActionSensor(CoordinatorEntity, SensorEntity):
    """Status of the optimization."""

    def __init__(self, coordinator: BatteryPlannerCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_action"
        self._attr_name = "Battery Planner Action"

    @property
    def native_value(self) -> str | None:
        """Return the status."""
        return self.coordinator.data.get('action_type')


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
            try:
                # Parse the GMT datetime string
                entry_time = datetime.strptime(entry['time'], '%a, %d %b %Y %H:%M:%S GMT')
                if entry_time >= now:
                    current_entry = entry
                    break
            except ValueError as e:
                _LOGGER.error("Error parsing datetime: %s for entry: %s", e, entry)
                continue

        if current_entry:
            return f"{current_entry['watts']}W at {current_entry['time']} (Price: {current_entry['price']})"
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the full schedule."""
        return {'schedule': self.coordinator.data.get('schedule', [])}


class BatteryPlannerScheduleInfoSensor(CoordinatorEntity, SensorEntity):
    """Additional schedule information."""

    def __init__(self, coordinator: BatteryPlannerCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_schedule_info"
        self._attr_name = "Battery Planner Schedule Info"

    @property
    def native_value(self) -> str | None:
        """Return the schedule info."""
        return self.coordinator.data.get('schedule_info')


class BatteryPlannerEnergyCostSensor(CoordinatorEntity, SensorEntity):
    """Energy cost component of the optimization."""

    def __init__(self, coordinator: BatteryPlannerCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_energy_cost"
        self._attr_name = "Battery Planner Energy Cost"
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float | None:
        """Return the energy cost."""
        return self.coordinator.data.get('energy_cost')


class BatteryPlannerNetworkCostSensor(CoordinatorEntity, SensorEntity):
    """Network cost component of the optimization."""

    def __init__(self, coordinator: BatteryPlannerCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_network_cost"
        self._attr_name = "Battery Planner Network Cost"
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float | None:
        """Return the network cost."""
        return self.coordinator.data.get('network_cost')


class BatteryPlannerCyclingCostSensor(CoordinatorEntity, SensorEntity):
    """Battery cycling cost component of the optimization."""

    def __init__(self, coordinator: BatteryPlannerCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_cycling_cost"
        self._attr_name = "Battery Planner Cycling Cost"
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float | None:
        """Return the cycling cost."""
        return self.coordinator.data.get('cycling_cost')


class BatteryPlannerTotalCostSensor(CoordinatorEntity, SensorEntity):
    """Total cost of the optimization."""

    def __init__(self, coordinator: BatteryPlannerCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_total_cost"
        self._attr_name = "Battery Planner Total Cost"
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float | None:
        """Return the total cost."""
        return self.coordinator.data.get('total_cost')


class BatteryPlannerBaselineCostSensor(CoordinatorEntity, SensorEntity):
    """Baseline cost without optimization."""

    def __init__(self, coordinator: BatteryPlannerCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_baseline_cost"
        self._attr_name = "Battery Planner Baseline Cost"
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float | None:
        """Return the baseline cost."""
        return self.coordinator.data.get('baseline_cost')