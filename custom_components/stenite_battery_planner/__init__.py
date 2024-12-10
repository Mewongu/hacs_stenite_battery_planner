# custom_components/stenite_battery_planner/__init__.py
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import voluptuous as vol
import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)
from homeassistant.const import CONF_NAME

DOMAIN = "stenite_battery_planner"
_LOGGER = logging.getLogger(__name__)

# Default values
DEFAULT_NAME = "Battery Planner"
DEFAULT_SECONDS_TO_SEARCH = 15
DEFAULT_BATTERY_ALLOW_EXPORT = False

# Configuration schema
CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    })
}, extra=vol.ALLOW_EXTRA)

# Service call schema
CALL_SERVICE_SCHEMA = vol.Schema({
    vol.Required('endpoint'): cv.url,
    vol.Required('nordpool_area'): cv.string,
    vol.Required('mean_draw'): vol.Coerce(float),
    vol.Required('battery_capacity'): vol.Coerce(float),
    vol.Required('min_battery_soc'): vol.Coerce(float),
    vol.Required('max_battery_soc'): vol.Coerce(float),
    vol.Required('max_battery_discharge'): vol.Coerce(float),
    vol.Required('max_battery_charge'): vol.Coerce(float),
    vol.Required('battery_soc'): vol.Coerce(float),
    vol.Required('cycle_cost'): vol.Coerce(float),
    vol.Optional('battery_allow_export', default=DEFAULT_BATTERY_ALLOW_EXPORT): cv.boolean,
    vol.Optional('seconds_to_search', default=DEFAULT_SECONDS_TO_SEARCH): cv.positive_int,
})


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Stenite Battery Planner Integration."""
    conf = config.get(DOMAIN, {})
    name = conf.get(CONF_NAME, DEFAULT_NAME)

    # Create the data coordinator
    coordinator = BatteryPlannerCoordinator(hass, name)

    # Store coordinator in hass.data for sensor platform to access
    hass.data[DOMAIN] = coordinator

    # Register the service to trigger updates
    async def plan_battery(call):
        """Handle the battery planning service call."""
        # Prepare payload from service call data
        payload = {
            'nordpool_area': call.data['nordpool_area'],
            'mean_draw': call.data['mean_draw'],
            'battery_capacity': call.data['battery_capacity'],
            'min_battery_soc': call.data['min_battery_soc'],
            'max_battery_soc': call.data['max_battery_soc'],
            'max_battery_discharge': call.data['max_battery_discharge'],
            'max_battery_charge': call.data['max_battery_charge'],
            'battery_soc': call.data['battery_soc'],
            'battery_allow_export': call.data.get('battery_allow_export', DEFAULT_BATTERY_ALLOW_EXPORT),
            'seconds_to_search': call.data.get('seconds_to_search', DEFAULT_SECONDS_TO_SEARCH),
            'cycle_cost': call.data['cycle_cost'],
        }

        # Update coordinator with endpoint and payload
        coordinator.endpoint = call.data['endpoint']
        coordinator.payload = payload

        # Trigger an update
        await coordinator.async_request_refresh()

    # Register the service
    hass.services.async_register(
        DOMAIN,
        'plan',
        plan_battery,
        schema=CALL_SERVICE_SCHEMA
    )

    # Add sensor platform
    hass.async_create_task(
        hass.helpers.discovery.async_load_platform(
            'sensor',
            DOMAIN,
            {},
            config
        )
    )

    return True


class BatteryPlannerCoordinator(DataUpdateCoordinator):
    """Coordinator for fetching battery plan data."""

    def __init__(
            self,
            hass: HomeAssistant,
            name: str
    ):
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{name} Coordinator"
        )
        self.endpoint: Optional[str] = None
        self.payload: Dict[str, Any] = {}
        self._last_plan: Dict[str, Any] = {}

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from endpoint."""
        if not self.endpoint or not self.payload:
            return {}

        try:
            session = async_get_clientsession(self.hass)
            async with session.post(
                    self.endpoint,
                    json=self.payload
            ) as response:
                if response.status == 200:
                    self._last_plan = await response.json()
                    return self._last_plan
                else:
                    error_text = await response.text()
                    _LOGGER.error(f"Battery planning failed with status {response.status}: {error_text}")
                    return self._last_plan
        except Exception as e:
            _LOGGER.error(f"Error in battery planning: {e}")
            return self._last_plan