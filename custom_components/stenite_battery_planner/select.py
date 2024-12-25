from __future__ import annotations
import logging
from typing import Dict

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from homeassistant.helpers.update_coordinator import CoordinatorEntity


from . import DOMAIN, PLANNER_INPUT_PARAMS, BatteryPlannerCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Battery Planner selector platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    if coordinator is None:
        _LOGGER.error("No Battery Planner coordinator found")
        return

    entities = []

    for d in PLANNER_INPUT_PARAMS:
        if d["entity_type"] == "option":
            entities.append(BatteryPlannerSelectEntity(coordinator, d))

    async_add_entities(entities)

class BatteryPlannerSelectEntity(CoordinatorEntity, SelectEntity):
    def __init__(self, coordinator: BatteryPlannerCoordinator, attributes: Dict[str, any]):
        """Initialize the select entity."""
        super().__init__(coordinator)
       
        self._device_id = f"{DOMAIN}"
        
        # Attributes ...
        self._attr_unique_id = f"{self._device_id}_{attributes["id"]}"
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
        
        # Update the option in your device/service
        self._current_option = option

        # Implement actual value setting logic with your device/service
        await self.coordinator.set_param(self._param_id, option)
        self.async_write_ha_state()

    @property
    def device_info(self):
        """Return device information."""
        return DeviceInfo(
            identifiers={(self._device_id)},
            name="Your Device Name"
        )
