"""Support for Stenite Battery Planner sensors."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN, BatteryPlannerCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Stenite Battery Planner sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        BatteryPlannerActionSensor(coordinator, entry),
        BatteryPlannerPowerSensor(coordinator, entry),
        BatteryPlannerSavingsSensor(coordinator, entry),
        BatteryPlannerScheduleSensor(coordinator, entry),
    ]

    async_add_entities(entities)

class BatteryPlannerBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for Stenite Battery Planner sensors."""

    def __init__(
        self,
        coordinator: BatteryPlannerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the base sensor."""
        super().__init__(coordinator)

        # Set up base entity properties
        self._attr_has_entity_name = True
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.title,
            manufacturer="Stenite",
        )

class BatteryPlannerActionSensor(BatteryPlannerBaseSensor):
    """Sensor for the current recommended battery action."""

    def __init__(
        self,
        coordinator: BatteryPlannerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_current_action"
        self._attr_name = "Current Recommended Action"
        self._valid_states = ["charge", "discharge", "idle", "self_consumption"]

    @property
    def native_value(self) -> StateType:
        """Return the current recommended action."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("action_type")

class BatteryPlannerPowerSensor(BatteryPlannerBaseSensor):
    """Sensor for the current recommended power setting."""

    def __init__(
        self,
        coordinator: BatteryPlannerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_current_power"
        self._attr_name = "Current Recommended Power"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> StateType:
        """Return the current recommended power in watts."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("watts")

class BatteryPlannerSavingsSensor(BatteryPlannerBaseSensor):
    """Sensor for tracking expected savings."""

    def __init__(
        self,
        coordinator: BatteryPlannerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_expected_savings"
        self._attr_name = "Expected Savings"

    @property
    def native_value(self) -> StateType:
        """Return the expected savings as a float."""
        if not self.coordinator.data:
            return None

        total_cost = self.coordinator.data.get("total_cost")
        baseline_cost = self.coordinator.data.get("baseline_cost")

        if total_cost is None or baseline_cost is None:
            return None

        # Convert the result to float
        return float(baseline_cost - total_cost)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if not self.coordinator.data:
            return {}

        return {
            "baseline_cost": float(self.coordinator.data.get("baseline_cost", 0.0)),
            "total_cost": float(self.coordinator.data.get("total_cost", 0.0)),
        }


class BatteryPlannerScheduleSensor(BatteryPlannerBaseSensor):
    """Sensor for the battery schedule status."""

    _attr_should_poll = False  # Prevent state recording

    def __init__(
            self,
            coordinator: BatteryPlannerCoordinator,
            entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_schedule"
        self._attr_name = "Battery Schedule Status"

    @property
    def native_value(self) -> StateType:
        """Return a summary of the schedule."""
        if not self.coordinator.data or "schedule" not in self.coordinator.data:
            return "No schedule"
        return f"{len(self.coordinator.data['schedule'])} periods planned"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return minimal attributes."""
        if not self.coordinator.data or "schedule" not in self.coordinator.data:
            return {}

        schedule = self.coordinator.data.get("schedule", [])
        return {
            "schedule": schedule,
        }