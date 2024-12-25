"""Support for Stenite Battery Planner select entities."""
from __future__ import annotations

import logging
from typing import Dict

from homeassistant.components.select import SelectEntity
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
    """Set up the Battery Planner select platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    if coordinator is None:
        _LOGGER.error("No Battery Planner coordinator found")
        return

    entities = []

    for d in PLANNER_INPUT_PARAMS:
        if d["entity_type"] == "option":
            entities.append(BatteryPlannerSelectEntity(coordinator, entry, d))

    async_add_entities(entities)

class BatteryPlannerSelectEntity(CoordinatorEntity, SelectEntity):
    """Select entity for battery planner options."""

    def __init__(
        self,
        coordinator: BatteryPlannerCoordinator,
        entry: ConfigEntry,
        attributes: Dict[str, any]
    ):
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._entry = entry

        # Set up entity properties
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{entry.entry_id}_{attributes['id']}"
        self._attr_name = attributes["name"]
        self._attr_options = attributes["options"]

        # Coordinator param link
        self._param_id = attributes["api_id"]

        # Current selected option
        self._current_option = self._attr_options[0]

    @property
    def current_option(self):
        """Return the current selected option."""
        return self._current_option

    async def async_select_option(self, option: str):
        """Change the selected option."""
        if option not in self._attr_options:
            raise ValueError(f"Invalid option: {option}")

        self._current_option = option
        await self.coordinator.set_param(self._param_id, option)
        self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.title,
            manufacturer="Stenite",
        )