"""Support for Stenite Battery Planner number entities."""
from __future__ import annotations

import logging
from typing import Dict

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN, PLANNER_INPUT_PARAMS, BatteryPlannerCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Battery Planner number platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    if coordinator is None:
        _LOGGER.error("No Battery Planner coordinator found")
        return

    entities = []

    for d in PLANNER_INPUT_PARAMS:
        if d["entity_type"] == "number":
            entities.append(BatteryPlannerInputNumber(coordinator, entry, d))

    async_add_entities(entities)


class BatteryPlannerInputNumber(CoordinatorEntity, NumberEntity):
    """Number entity for battery planner input parameters."""

    def __init__(
            self,
            coordinator: BatteryPlannerCoordinator,
            entry: ConfigEntry,
            attributes: Dict[str, any]
    ):
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._entry = entry

        # Set up entity properties
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{entry.entry_id}_{attributes['id']}"
        self._attr_name = attributes["name"]

        # Define entity properties
        self._attr_min_value = attributes["min_value"]  # Minimum allowed value
        self._attr_max_value = attributes["max_value"]  # Maximum allowed value
        self._attr_step = attributes["step_value"]  # Step size
        self._attr_native_unit_of_measurement = attributes["unit"]  # Optional

        # Coordinator param link
        self._param_id = attributes["api_id"]

        # Current value
        self._value = 0

    @property
    def native_value(self) -> int | float | None:
        """Return the current value."""
        return self._value

    async def async_set_native_value(self, value: int | float):
        """Update the current value."""
        self._value = value
        await self.coordinator.set_param(self._param_id, value)
        self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.title,
            manufacturer="Stenite",
        )