# custom_components/stenite_battery_planner/__init__.py
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import voluptuous as vol
import aiohttp

from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
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
DEFAULT_BATTERY_ALLOW_EXPORT = False

# Configuration schema
CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    })
}, extra=vol.ALLOW_EXTRA)

# Updated service call schema to match new API
CALL_SERVICE_SCHEMA = vol.Schema({
    vol.Optional('nordpool_area'): cv.string,
    vol.Optional('mean_draw'): vol.Coerce(float),  # kW
    vol.Optional('battery_capacity'): vol.Coerce(float),  # kWh
    vol.Optional('battery_min_soc'): vol.Coerce(int),  # percentage
    vol.Optional('battery_max_soc'): vol.Coerce(int),  # percentage
    vol.Optional('battery_max_discharge'): vol.Coerce(float),  # kW
    vol.Optional('battery_min_discharge'): vol.Coerce(float),  # kW
    vol.Optional('battery_max_charge'): vol.Coerce(float),  # kW
    vol.Optional('battery_min_charge'): vol.Coerce(float),  # kW
    vol.Optional('battery_soc'): vol.Coerce(int),  # percentage
    vol.Optional('battery_cycle_cost'): vol.Coerce(float),  # Currency per cycle
    vol.Optional('network_charge_kWh'): vol.Coerce(float),  # Currency per kWh
    vol.Optional('battery_allow_export', default=DEFAULT_BATTERY_ALLOW_EXPORT): cv.boolean,
})

PLANNER_API_PARAM_ID = [
    'nordpool_area',
    'mean_draw',
    'battery_capacity',
    'battery_min_soc',
    'battery_max_soc',
    'battery_min_discharge',
    'battery_max_discharge',
    'battery_min_charge',
    'battery_max_charge',
    'battery_soc',
    'battery_allow_export',
    'battery_cycle_cost',
    'network_charge_kWh',
]

PLANNER_INPUT_PARAMS = [
    {"api_id": 'nordpool_area', "id": 'nordpool_area', "name": 'Nordpool Area', "entity_type": 'option', "options": ["SE1", "SE2", "SE3", "SE4"]},
    {"api_id": None, "id": 'currency', "name": 'Nordpool Currency', "entity_type": 'option', "options": ["SEK", "SEK2", "SEK3", "SEK4"]},
    {"api_id": 'battery_allow_export', "id": 'allow_battery_to_grid_export', "name": 'Allow Export To Grid', "entity_type": 'option', "options": [True, False]},
    {"api_id": 'battery_capacity', "id": 'battery_capacity', "name": 'Total Battery Capacity', "entity_type": 'number', "min_value": 0.0, "max_value": 10000.0, "step_value": 0.1, "unit": 'kWh'},
    {"api_id": 'battery_max_soc', "id": 'max_battery_soc', "name": 'Maximum Battery State of Charge', "entity_type": 'number', "min_value": 0, "max_value": 100, "step_value": 1, "unit": 'percent'},
    {"api_id": 'battery_min_soc', "id": 'min_battery_soc', "name": 'Minimum Battery State of Charge', "entity_type": 'number', "min_value": 0, "max_value": 100, "step_value": 1, "unit": 'percent'},
    {"api_id": 'battery_soc', "id": 'current_battery_soc', "name": 'Current Battery State of Charge', "entity_type": 'number', "min_value": 0, "max_value": 100, "step_value": 1, "unit": 'percent'},
    {"api_id": 'battery_min_discharge', "id": 'min_battery_discharge_power', "name": 'Minimum Battery Discharge Power', "entity_type": 'number', "min_value": 0.0, "max_value": 100.0, "step_value": 0.1, "unit": 'kW'},
    {"api_id": 'battery_max_discharge', "id": 'max_battery_discharge_power', "name": 'Maximum Battery Discharge Power', "entity_type": 'number', "min_value": 0.0, "max_value": 100.0, "step_value": 0.1, "unit": 'kW'},
    {"api_id": 'battery_min_charge', "id": 'min_battery_charge_power', "name": 'Minimum Battery Charge Power', "entity_type": 'number', "min_value": 0.0, "max_value": 100.0, "step_value": 0.1, "unit": 'kW'},
    {"api_id": 'battery_max_charge', "id": 'max_battery_charge_power', "name": 'Maximum Battery Charge Power', "entity_type": 'number', "min_value": 0.0, "max_value": 100.0, "step_value": 0.1, "unit": 'kW'},
    {"api_id": 'battery_cycle_cost', "id": 'battery_full_cycle_cost', "name": 'Full Battery Charge Cycle Cost', "entity_type": 'number', "min_value": 0.0, "max_value": 100.0, "step_value": 0.1, "unit": 'currency'},
    {"api_id": 'mean_draw', "id": 'mean_power_consumption', "name": 'Mean Power Consumption', "entity_type": 'number', "min_value": 0.0, "max_value": 100.0, "step_value": 0.1, "unit": 'kW'},
    {"api_id": 'network_charge_kWh', "id": 'grid_utility_import_cost', "name": 'Grid Utility Energy Import Cost', "entity_type": 'number', "min_value": 0.0, "max_value": 100.0, "step_value": 0.1, "unit": 'currency'},
]

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Stenite Battery Planner Integration."""
    conf = config.get(DOMAIN, {})
    name = conf.get(CONF_NAME, DEFAULT_NAME)

    # Create the data coordinator
    coordinator = BatteryPlannerCoordinator(hass, name)

    # Store coordinator in hass.data for sensor platform to access
    hass.data[DOMAIN] = coordinator

    # Register the service to trigger updates
    async def plan_battery(call: ServiceCall) -> ServiceResponse:
        """Handle the battery planning service call."""
        # Prepare payload from service call data
        payload = {}
        for param in PLANNER_API_PARAM_ID:
            if param in call.data:
                payload[param] = call.data[param]
            else:
                payload[param] = await coordinator.get_param_value(param)               

        # payload = {
        #     'nordpool_area': (call.data['nordpool_area'] if call.data['nordpool_area'] not None else 1),
        #     'mean_draw': call.data['mean_draw'],
        #     'battery_capacity': call.data['battery_capacity'],
        #     'battery_min_soc': call.data['battery_min_soc'],
        #     'battery_max_soc': call.data['battery_max_soc'],
        #     'battery_max_discharge': call.data['battery_max_discharge'],
        #     'battery_min_discharge': call.data['battery_min_discharge'],
        #     'battery_max_charge': call.data['battery_max_charge'],
        #     'battery_min_charge': call.data['battery_min_charge'],
        #     'battery_soc': call.data['battery_soc'],
        #     'battery_allow_export': call.data.get('battery_allow_export', DEFAULT_BATTERY_ALLOW_EXPORT),
        #     'battery_cycle_cost': call.data['battery_cycle_cost'],
        #     'network_charge_kWh': call.data['network_charge_kWh'],
        # }

        # Update coordinator with endpoint and payload
        coordinator.endpoint = "https://batteryplanner.stenite.com/api/v2.0/plan"
        coordinator.payload = payload

        # Trigger an update
        plan = await coordinator.get_plan()
        if len(plan) < 0:
            plan = {"dummy" : "return"}
        return plan

    # Register the service
    hass.services.async_register(
        DOMAIN,
        'plan',
        plan_battery,
        schema=CALL_SERVICE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    # Add number platform
    hass.async_create_task(
        hass.helpers.discovery.async_load_platform(
            'number',
            DOMAIN,
            {},
            config
        )
    )

    # Add select platform
    hass.async_create_task(
        hass.helpers.discovery.async_load_platform(
            'select',
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

        # Input parameters
        self._params = {
            "nordpool_area": "SE3",
            "mean_draw": 0.0,
            "battery_capacity": 0.0,
            "battery_min_soc": 0,
            "battery_max_soc": 100,
            "battery_max_discharge": 1.0,
            "battery_min_discharge": 1.0,
            "battery_max_charge": 1.0,
            "battery_min_charge": 1.0,
            "battery_soc": 50,
            "battery_allow_export": True,
            "battery_cycle_cost": 0.0,
            "network_charge_kWh": 0.0,
        }

        self._last_plan: Dict[str, Any] = {}

    async def get_plan(self) -> Dict[str, Any]:
        """Fetch data from endpoint."""
        if not self.endpoint or not self.payload:
            return {}

        try:
            session = async_get_clientsession(self.hass)
            _LOGGER.error(f"Trying to plan with the following input {self.payload}")
            async with session.post(
                    self.endpoint,
                    json=self.payload
            ) as response:
                if response.status == 200:
                    self._last_plan = await response.json()
                    return self._last_plan
                else:
                    error_text = await response.text()
                    _LOGGER.error(f"Battery planning failed with status {response.status}: {error_text}\n when connecting to {self.endpoint}")
                    return {}
        except Exception as e:
            _LOGGER.error(f"Error in battery planning: {e}")
            return {}

    # Should use entity data to create the payload, not reuse the existing payload...
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
                    _LOGGER.error(f"Battery planning failed with status {response.status}: {error_text}\n when connecting to {self.endpoint}")
                    return self._last_plan
        except Exception as e:
            _LOGGER.error(f"Error in battery planning: {e}")
            return self._last_plan
    
    async def set_param(self, param: str, value) -> int:
        return_value = None
        try:
            self._params[param] = value
            return_value = self._params[param]
        except Exception as e:
            _LOGGER.error(f"Error when setting planning parameter: {e}")
        return return_value
    
    async def get_param_value(self, param: str) -> str | int | float:
        _LOGGER.error(f"Get param: {self._params[param]}")
        return self._params[param]
