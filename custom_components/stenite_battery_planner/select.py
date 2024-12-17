from __future__ import annotations
import logging
from typing import Dict, Final

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN, PLANNER_INPUT_PARAMS, BatteryPlannerCoordinator

_LOGGER = logging.getLogger(__name__)

# Constants for select options
NORDPOOL_AREAS: Final = ["SE1", "SE2", "SE3", "SE4"]
EXPORT_OPTIONS: Final = [True, False]


async def async_setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        async_add_entities: AddEntitiesCallback,
        discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the Battery Planner select platform."""
    coordinator = hass.data.get(DOMAIN)

    if coordinator is None:
        _LOGGER.error("No Battery Planner coordinator found")
        return

    entities = [
        BatteryPlannerSelectEntity(coordinator, params)
        for params in PLANNER_INPUT_PARAMS
        if params["entity_type"] == "option"
    ]

    async_add_entities(entities)


class BatteryPlannerSelectEntity(CoordinatorEntity, SelectEntity):
    """Represents a selection input parameter for the battery planner."""

    def __init__(self, coordinator: BatteryPlannerCoordinator, attributes: Dict[str, any]):
        """Initialize the select entity."""
        super().__init__(coordinator)

        # Basic attributes
        self._attr_unique_id = f"{DOMAIN}_{attributes['id']}"
        self._attr_name = attributes["name"]
        self._attr_entity_category = EntityCategory.CONFIG

        # Options setup
        self._attr_options = [str(opt) for opt in attributes["options"]]  # Convert all options to strings

        # Coordinator param link
        self._param_id = attributes["api_id"]

        # Device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "battery_planner")},
            name="Battery Planner",
            manufacturer="Stenite",
            model="Battery Planner v2",
            sw_version="2.0"
        )

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        try:
            value = self.coordinator._params[self._param_id]
            return str(value)  # Convert to string for consistency
        except (KeyError, AttributeError):
            return None

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        try:
            # Convert the option to the appropriate type based on the parameter
            if self._param_id == 'battery_allow_export':
                value = option.lower() == 'true'  # Convert string to boolean
            else:
                value = option  # Keep as string for other parameters

            # Update the value in coordinator
            await self.coordinator.set_param(self._param_id, value)
            self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error(f"Error setting option for {self.name}: {str(e)}")
            raise

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return True  # Always available as it's a configuration entity

    @property
    def should_poll(self) -> bool:
        """Return if entity should be polled."""
        return False  # No polling needed for configuration entities