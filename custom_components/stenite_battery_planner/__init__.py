# custom_components/stenite_battery_planner/__init__.py
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, Dict, Optional

import voluptuous as vol
import aiohttp
from homeassistant.config_entries import ConfigEntry

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
        vol.Optional("nordpool_area", default="SE3"): cv.string,
        vol.Optional("mean_draw", default=2.0): vol.All(
            vol.Coerce(float),
            vol.Any(vol.Equal(0), lambda v: validate_positive_float(v, "mean_draw"))
        ),
        vol.Optional("battery_capacity", default=10.0): vol.All(
            vol.Coerce(float),
            lambda v: validate_positive_float(v, "battery_capacity")
        ),
        vol.Optional("battery_min_soc", default=20): vol.All(
            vol.Coerce(float),
            lambda v: validate_percentage(v, "battery_min_soc")
        ),
        vol.Optional("battery_max_soc", default=80): vol.All(
            vol.Coerce(float),
            lambda v: validate_percentage(v, "battery_max_soc")
        ),
        vol.Optional("battery_min_discharge", default=0.0): vol.All(
            vol.Coerce(float),
            lambda v: validate_positive_or_zero_float(v, "battery_min_discharge")
        ),
        vol.Optional("battery_max_discharge", default=1.0): vol.All(
            vol.Coerce(float),
            lambda v: validate_positive_float(v, "battery_max_discharge")
        ),
        vol.Optional("battery_min_charge", default=0.0): vol.All(
            vol.Coerce(float),
            lambda v: validate_positive_or_zero_float(v, "battery_min_charge")
        ),
        vol.Optional("battery_max_charge", default=1.0): vol.All(
            vol.Coerce(float),
            lambda v: validate_positive_float(v, "battery_max_charge")
        ),
        vol.Optional("battery_soc", default=50): vol.All(
            vol.Coerce(float),
            lambda v: validate_percentage(v, "battery_soc")
        ),
        vol.Optional("battery_cycle_cost", default=0.3): vol.All(
            vol.Coerce(float),
            lambda v: validate_positive_float(v, "battery_cycle_cost")
        ),
        vol.Optional("battery_allow_export", default=True): cv.boolean,
        vol.Optional("network_charge_kWh", default=0.3): vol.All(
            vol.Coerce(float),
            lambda v: validate_positive_float(v, "network_charge_kWh")
        ),
        vol.Optional("stored_value_per_kWh", default=0.3): vol.All(
            vol.Coerce(float),
            lambda v: validate_positive_float(v, "stored_value_per_kWh")
        ),
    })
}, extra=vol.ALLOW_EXTRA)

def validate_positive_float(value: float, name: str) -> None:
    """Validate that a value is a positive float."""
    if not isinstance(value, (int, float)):
        raise vol.Invalid(f"{name} must be a number")
    if float(value) <= 0:
        raise vol.Invalid(f"{name} must be greater than 0")
    return float(value)
def validate_positive_or_zero_float(value: float, name: str) -> None:
    """Validate that a value is a positive float."""
    if not isinstance(value, (int, float)):
        raise vol.Invalid(f"{name} must be a number")
    if float(value) < 0:
        raise vol.Invalid(f"{name} must be greater or equal to 0")
    return float(value)

def validate_percentage(value: float, name: str) -> None:
    """Validate that a value is a percentage (0-100)."""
    if not isinstance(value, (int, float)):
        raise vol.Invalid(f"{name} must be a number")
    if float(value) < 0 or float(value) > 100:
        raise vol.Invalid(f"{name} must be between 0 and 100")
    return float(value)

# Updated service call schema to match new API
CALL_SERVICE_SCHEMA = vol.Schema({
    vol.Optional('nordpool_area'): cv.string,
    vol.Optional('mean_draw'): vol.All(
        vol.Coerce(float),
        vol.Any(vol.Equal(0), lambda v: validate_positive_float(v, "mean_draw"))
    ),
    vol.Optional('battery_capacity'): vol.All(
        vol.Coerce(float),
        lambda v: validate_positive_float(v, "battery_capacity")
    ),
    vol.Optional('battery_min_soc'): vol.All(
        vol.Coerce(float),
        lambda v: validate_percentage(v, "battery_min_soc")
    ),
    vol.Optional('battery_max_soc'): vol.All(
        vol.Coerce(float),
        lambda v: validate_percentage(v, "battery_max_soc")
    ),
    vol.Optional('battery_max_discharge'): vol.All(
        vol.Coerce(float),
        lambda v: validate_positive_float(v, "battery_max_discharge")
    ),
    vol.Optional('battery_min_discharge'): vol.All(
        vol.Coerce(float),
        lambda v: validate_positive_or_zero_float(v, "battery_min_discharge")
    ),
    vol.Optional('battery_max_charge'): vol.All(
        vol.Coerce(float),
        lambda v: validate_positive_float(v, "battery_max_charge")
    ),
    vol.Optional('battery_min_charge'): vol.All(
        vol.Coerce(float),
        lambda v: validate_positive_or_zero_float(v, "battery_min_charge")
    ),
    vol.Optional('battery_soc'): vol.All(
        vol.Coerce(float),
        lambda v: validate_percentage(v, "battery_soc")
    ),
    vol.Optional('battery_cycle_cost'): vol.All(
        vol.Coerce(float),
        lambda v: validate_positive_float(v, "battery_cycle_cost")
    ),
    vol.Optional('network_charge_kWh'): vol.All(
        vol.Coerce(float),
        lambda v: validate_positive_float(v, "network_charge_kWh")
    ),
    vol.Optional('battery_allow_export', default=DEFAULT_BATTERY_ALLOW_EXPORT): cv.boolean,
    vol.Optional('stored_value_per_kWh'): vol.All(
        vol.Coerce(float),
        lambda v: validate_positive_float(v, "stored_value_per_kWh")
    ),
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
    'stored_value_per_kWh',
]

PLANNER_INPUT_PARAMS = [
    {"api_id": 'nordpool_area', "id": 'nordpool_area', "name": 'Nordpool Area', "entity_type": 'option', "options": ["SE1", "SE2", "SE3", "SE4"]},
    {"api_id": None, "id": 'currency', "name": 'Nordpool Currency', "entity_type": 'option', "options": ["SEK", "SEK2", "SEK3", "SEK4"]},
    {"api_id": 'battery_allow_export', "id": 'allow_battery_to_grid_export', "name": 'Allow Export To Grid', "entity_type": 'option', "options": [True, False]},
    {"api_id": 'battery_capacity', "id": 'battery_capacity', "name": 'Total Battery Capacity', "entity_type": 'number', "min_value": 0.0, "max_value": 10000.0, "step_value": 0.001, "unit": 'kWh'},
    {"api_id": 'battery_max_soc', "id": 'max_battery_soc', "name": 'Maximum Battery State of Charge', "entity_type": 'number', "min_value": 0, "max_value": 100, "step_value": 1, "unit": 'percent'},
    {"api_id": 'battery_min_soc', "id": 'min_battery_soc', "name": 'Minimum Battery State of Charge', "entity_type": 'number', "min_value": 0, "max_value": 100, "step_value": 1, "unit": 'percent'},
    {"api_id": 'battery_soc', "id": 'current_battery_soc', "name": 'Current Battery State of Charge', "entity_type": 'number', "min_value": 0, "max_value": 100, "step_value": 0.01, "unit": 'percent'},
    {"api_id": 'battery_min_discharge', "id": 'min_battery_discharge_power', "name": 'Minimum Battery Discharge Power', "entity_type": 'number', "min_value": 0.0, "max_value": 100.0, "step_value": 0.001, "unit": 'kW'},
    {"api_id": 'battery_max_discharge', "id": 'max_battery_discharge_power', "name": 'Maximum Battery Discharge Power', "entity_type": 'number', "min_value": 0.0, "max_value": 100.0, "step_value": 0.001, "unit": 'kW'},
    {"api_id": 'battery_min_charge', "id": 'min_battery_charge_power', "name": 'Minimum Battery Charge Power', "entity_type": 'number', "min_value": 0.0, "max_value": 100.0, "step_value": 0.001, "unit": 'kW'},
    {"api_id": 'battery_max_charge', "id": 'max_battery_charge_power', "name": 'Maximum Battery Charge Power', "entity_type": 'number', "min_value": 0.0, "max_value": 100.0, "step_value": 0.001, "unit": 'kW'},
    {"api_id": 'battery_cycle_cost', "id": 'battery_full_cycle_cost', "name": 'Full Battery Charge Cycle Cost', "entity_type": 'number', "min_value": 0.0, "max_value": 100.0, "step_value": 0.001, "unit": 'currency'},
    {"api_id": 'mean_draw', "id": 'mean_power_consumption', "name": 'Mean Power Consumption', "entity_type": 'number', "min_value": 0.0, "max_value": 100.0, "step_value": 0.001, "unit": 'kW'},
    {"api_id": 'network_charge_kWh', "id": 'grid_utility_import_cost', "name": 'Grid Utility Energy Import Cost', "entity_type": 'number', "min_value": 0.0, "max_value": 100.0, "step_value": 0.001, "unit": 'currency'},
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Stenite Battery Planner from a config entry."""
    coordinator = BatteryPlannerCoordinator(hass, entry.data[CONF_NAME])

    # Initialize coordinator parameters with config values
    for param in PLANNER_API_PARAM_ID:
        if param in entry.data:
            await coordinator.set_param(param, entry.data[param])

    # Store coordinator in hass.data using the entry_id
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Perform initial data fetch
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, ["number", "select", "sensor"])

    # Only register service if it hasn't been registered yet
    if not hass.services.has_service(DOMAIN, 'plan'):
        async def plan_battery(call: ServiceCall) -> ServiceResponse:
            """Handle the battery planning service call."""
            # Get the coordinator for this instance
            coordinator = next(iter(hass.data[DOMAIN].values()))

            # Build payload from current parameter values
            payload = {}
            for param in PLANNER_API_PARAM_ID:
                if param in call.data:
                    # Update coordinator with new value from service call
                    await coordinator.set_param(param, call.data[param])
                payload[param] = await coordinator.get_param_value(param)

            await coordinator.validate_dependent_values(payload)
            coordinator.endpoint = "https://batteryplanner.stenite.com/api/v2.0/plan"
            coordinator.payload = payload

            # Trigger an immediate data update
            await coordinator.async_refresh()

            # Return the plan data
            return coordinator.data if coordinator.data else {"error": "Failed to fetch plan"}

        hass.services.async_register(
            DOMAIN,
            'plan',
            plan_battery,
            schema=CALL_SERVICE_SCHEMA,
            supports_response=SupportsResponse.ONLY,
        )

    async def get_schedule(call: ServiceCall) -> ServiceResponse:
        """Handle retrieving the current schedule."""
        coordinator = next(iter(hass.data[DOMAIN].values()))
        if not coordinator.data or "schedule" not in coordinator.data:
            return {"schedule": []}

        schedule = coordinator.data.get("schedule", [])
        formatted_schedule = []

        for period in schedule:
            formatted_schedule.append({
                "start_time": period.get("start_time"),
                "end_time": period.get("end_time"),
                "action": period.get("action"),
                "power": period.get("power"),
                "price": period.get("price"),
                "savings": period.get("savings")
            })

        return {"schedule": formatted_schedule}

    # Register the get_schedule service
    hass.services.async_register(
        DOMAIN,
        "get_schedule",
        get_schedule,
        supports_response=SupportsResponse.ONLY,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, ["number", "select", "sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


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
            name=f"{name} Coordinator",
            update_interval=timedelta(minutes=5),
        )
        self.endpoint: Optional[str] = "https://batteryplanner.stenite.com/api/v2.0/plan"
        self.payload: Dict[str, Any] = {}

        # Input parameters with default values
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
            "stored_value_per_kWh": 0.0,
        }

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from endpoint."""
        if not self.endpoint:
            return {}

        # Build payload from current parameter values
        self.payload = {param: self._params[param] for param in PLANNER_API_PARAM_ID}

        try:
            session = async_get_clientsession(self.hass)
            _LOGGER.debug(f"Planning request with payload: {self.payload}")

            async with session.post(
                    self.endpoint,
                    json=self.payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    _LOGGER.error(f"Battery planning failed with status {response.status}: {error_text}")
                    return {}
        except Exception as e:
            _LOGGER.error(f"Error in battery planning: {e}")
            return {}

    async def set_param(self, param: str, value) -> Any:
        """Set parameter value and trigger update."""
        try:
            self._params[param] = value
            # Schedule an update when parameters change
            await self.async_refresh()
            return self._params[param]
        except Exception as e:
            _LOGGER.error(f"Error when setting planning parameter: {e}")
            return None

    async def get_param_value(self, param: str) -> Any:
        """Get parameter value."""
        return self._params.get(param)

    async def validate_dependent_values(self, payload: Dict[str, Any]) -> None:
        """Validate interdependent values."""
        if ('battery_min_soc' in payload and 'battery_max_soc' in payload and
                payload['battery_min_soc'] > payload['battery_max_soc']):
            raise vol.Invalid("Minimum SOC cannot be greater than maximum SOC")

        if ('battery_min_discharge' in payload and 'battery_max_discharge' in payload and
                payload['battery_min_discharge'] > payload['battery_max_discharge']):
            raise vol.Invalid("Minimum discharge power cannot be greater than maximum discharge power")

        if ('battery_min_charge' in payload and 'battery_max_charge' in payload and
                payload['battery_min_charge'] > payload['battery_max_charge']):
            raise vol.Invalid("Minimum charge power cannot be greater than maximum charge power")

