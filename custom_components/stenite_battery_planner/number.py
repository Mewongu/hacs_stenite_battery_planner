from __future__ import annotations
import logging
from typing import Dict

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN, PLANNER_INPUT_PARAMS, BatteryPlannerCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        async_add_entities: AddEntitiesCallback,
        discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the Battery Planner number platform."""
    coordinator = hass.data.get(DOMAIN)

    if coordinator is None:
        _LOGGER.error("No Battery Planner coordinator found")
        return

    entities = [
        BatteryPlannerInputNumber(coordinator, params)
        for params in PLANNER_INPUT_PARAMS
        if params["entity_type"] == "number"
    ]

    async_add_entities(entities)


class BatteryPlannerInputNumber(CoordinatorEntity, NumberEntity):
    """Represents a numeric input parameter for the battery planner."""

    def __init__(self, coordinator: BatteryPlannerCoordinator, attributes: Dict[str, any]):
        """Initialize the number entity."""
        super().__init__(coordinator)

        self._attr_device_class = "power"  # Default device class
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_mode = NumberMode.BOX

        # Basic attributes
        self._attr_unique_id = f"{DOMAIN}_{attributes['id']}"
        self._attr_name = attributes["name"]

        # Value constraints
        self._attr_native_min_value = attributes["min_value"]
        self._attr_native_max_value = attributes["max_value"]
        self._attr_native_step = attributes["step_value"]
        self._attr_native_unit_of_measurement = attributes["unit"]

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
    def native_value(self) -> float | None:
        """Return the current value."""
        try:
            return self.coordinator._params[self._param_id]
        except (KeyError, AttributeError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        try:
            # Apply additional validation based on parameter type
            if self._param_id.endswith('_soc'):
                if not 0 <= value <= 100:
                    raise ValueError("State of charge must be between 0 and 100")

            elif self._param_id.endswith('_charge') or self._param_id.endswith('_discharge'):
                if value < 0:
                    raise ValueError("Power values must be non-negative")

            # Update the value in coordinator
            await self.coordinator.set_param(self._param_id, value)
            self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error(f"Error setting value for {self.name}: {str(e)}")
            raise

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return True  # Always available as it's a configuration entity

    @property
    def should_poll(self) -> bool:
        """Return if entity should be polled."""
        return False  # No polling needed for configuration entities