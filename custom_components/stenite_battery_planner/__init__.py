from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant.const import (
    CONF_NAME,
    Platform,
)
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.config_entries import ConfigEntry

DOMAIN = "stenite_battery_planner"
_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.NUMBER,
    Platform.SELECT,
]

# Default values
DEFAULT_NAME = "Battery Planner"
DEFAULT_BATTERY_ALLOW_EXPORT = False
API_ENDPOINT = "https://batteryplanner.stenite.com/api/v2/plan"

# Configuration schema
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

# Updated service call schema to match v2 API spec
CALL_SERVICE_SCHEMA = vol.Schema({
    vol.Required('nordpool_area'): cv.string,
    vol.Required('mean_draw'): vol.Coerce(float),
    vol.Required('battery_capacity'): vol.Coerce(float),
    vol.Required('battery_min_soc'): vol.All(
        vol.Coerce(float),
        vol.Range(min=0, max=100)
    ),
    vol.Required('battery_max_soc'): vol.All(
        vol.Coerce(float),
        vol.Range(min=0, max=100)
    ),
    vol.Required('battery_soc'): vol.All(
        vol.Coerce(float),
        vol.Range(min=0, max=100)
    ),
    vol.Required('battery_max_discharge'): vol.All(
        vol.Coerce(float),
        vol.Range(min=0)
    ),
    vol.Required('battery_min_discharge'): vol.All(
        vol.Coerce(float),
        vol.Range(min=0)
    ),
    vol.Required('battery_max_charge'): vol.All(
        vol.Coerce(float),
        vol.Range(min=0)
    ),
    vol.Required('battery_min_charge'): vol.All(
        vol.Coerce(float),
        vol.Range(min=0)
    ),
    vol.Required('battery_allow_export'): cv.boolean,
    vol.Required('battery_cycle_cost'): vol.Coerce(float),
    vol.Required('network_charge_kWh'): vol.Coerce(float),
})

PLANNER_INPUT_PARAMS = [
    {"api_id": 'nordpool_area', "id": 'nordpool_area', "name": 'Nordpool Area', "entity_type": 'option',
     "options": ["SE1", "SE2", "SE3", "SE4"]},
    {"api_id": 'battery_allow_export', "id": 'allow_battery_to_grid_export', "name": 'Allow Export To Grid',
     "entity_type": 'option', "options": [True, False]},
    {"api_id": 'battery_capacity', "id": 'battery_capacity', "name": 'Total Battery Capacity', "entity_type": 'number',
     "min_value": 0.0, "max_value": 10000.0, "step_value": 0.1, "unit": 'kWh'},
    {"api_id": 'battery_max_soc', "id": 'max_battery_soc', "name": 'Maximum Battery State of Charge',
     "entity_type": 'number', "min_value": 0, "max_value": 100, "step_value": 1, "unit": 'percent'},
    {"api_id": 'battery_min_soc', "id": 'min_battery_soc', "name": 'Minimum Battery State of Charge',
     "entity_type": 'number', "min_value": 0, "max_value": 100, "step_value": 1, "unit": 'percent'},
    {"api_id": 'battery_soc', "id": 'current_battery_soc', "name": 'Current Battery State of Charge',
     "entity_type": 'number', "min_value": 0, "max_value": 100, "step_value": 1, "unit": 'percent'},
    {"api_id": 'battery_min_discharge', "id": 'min_battery_discharge_power', "name": 'Minimum Battery Discharge Power',
     "entity_type": 'number', "min_value": 0.0, "max_value": 100.0, "step_value": 0.1, "unit": 'kW'},
    {"api_id": 'battery_max_discharge', "id": 'max_battery_discharge_power', "name": 'Maximum Battery Discharge Power',
     "entity_type": 'number', "min_value": 0.0, "max_value": 100.0, "step_value": 0.1, "unit": 'kW'},
    {"api_id": 'battery_min_charge', "id": 'min_battery_charge_power', "name": 'Minimum Battery Charge Power',
     "entity_type": 'number', "min_value": 0.0, "max_value": 100.0, "step_value": 0.1, "unit": 'kW'},
    {"api_id": 'battery_max_charge', "id": 'max_battery_charge_power', "name": 'Maximum Battery Charge Power',
     "entity_type": 'number', "min_value": 0.0, "max_value": 100.0, "step_value": 0.1, "unit": 'kW'},
    {"api_id": 'battery_cycle_cost', "id": 'battery_full_cycle_cost', "name": 'Full Battery Charge Cycle Cost',
     "entity_type": 'number', "min_value": 0.0, "max_value": 100.0, "step_value": 0.1, "unit": 'currency'},
    {"api_id": 'mean_draw', "id": 'mean_power_consumption', "name": 'Mean Power Consumption', "entity_type": 'number',
     "min_value": 0.0, "max_value": 100.0, "step_value": 0.1, "unit": 'kW'},
    {"api_id": 'network_charge_kWh', "id": 'grid_utility_import_cost', "name": 'Grid Utility Energy Import Cost',
     "entity_type": 'number', "min_value": 0.0, "max_value": 100.0, "step_value": 0.1, "unit": 'currency'},
]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Stenite Battery Planner Integration."""
    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]
    name = conf.get(CONF_NAME, DEFAULT_NAME)

    # Create the coordinator
    coordinator = BatteryPlannerCoordinator(hass, name)

    # Store coordinator in hass.data
    hass.data[DOMAIN] = {
        "coordinator": coordinator,
        "name": name,
    }

    # Register service
    async def plan_battery(call: ServiceCall) -> ServiceResponse:
        """Handle the battery planning service call."""
        try:
            payload = {param["api_id"]: await coordinator.get_param_value(param["api_id"])
                       for param in PLANNER_INPUT_PARAMS if param["api_id"]}

            payload.update({k: v for k, v in call.data.items() if k in payload})

            if payload['battery_min_soc'] > payload['battery_max_soc']:
                raise ValueError("Minimum SOC cannot be greater than maximum SOC")
            if payload['battery_min_discharge'] > payload['battery_max_discharge']:
                raise ValueError("Minimum discharge power cannot be greater than maximum discharge power")
            if payload['battery_min_charge'] > payload['battery_max_charge']:
                raise ValueError("Minimum charge power cannot be greater than maximum charge power")

            coordinator.endpoint = API_ENDPOINT
            coordinator.payload = payload

            plan = await coordinator.get_plan()
            if not plan:
                return {"error": "Failed to get battery plan"}
            return plan

        except Exception as e:
            _LOGGER.error(f"Error in battery planning service: {str(e)}")
            return {"error": str(e)}

    hass.services.async_register(
        DOMAIN,
        "plan",
        plan_battery,
        schema=CALL_SERVICE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    # Set up platforms
    await hass.async_create_task(
        async_load_platforms(hass, config)
    )

    return True


async def async_load_platforms(hass: HomeAssistant, config: ConfigType) -> None:
    """Load platforms with modern setup."""
    # Create a mock config entry since we're not using config flow
    mock_entry = ConfigEntry(
        entry_id="1",
        domain=DOMAIN,
        title="Battery Planner",
        data={},
        options={},
        version=1,
    )

    # Set up each platform
    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(mock_entry, platform)
        )


class BatteryPlannerCoordinator(DataUpdateCoordinator):
    """Coordinator for fetching battery plan data."""

    def __init__(self, hass: HomeAssistant, name: str):
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{name} Coordinator",
            update_interval=None  # Only update via service calls
        )
        self.endpoint: Optional[str] = None
        self.payload: Dict[str, Any] = {}

        # Initialize default parameters
        self._params = {param["api_id"]: (param["options"][0] if param["entity_type"] == "option" else 0)
                        for param in PLANNER_INPUT_PARAMS if param["api_id"]}

        self._last_plan: Dict[str, Any] = {}

    async def get_plan(self) -> Dict[str, Any]:
        """Fetch data from endpoint."""
        if not self.endpoint or not self.payload:
            return {}

        try:
            session = async_get_clientsession(self.hass)
            async with session.post(
                    self.endpoint,
                    json=self.payload,
                    raise_for_status=True
            ) as response:
                self._last_plan = await response.json()
                return self._last_plan

        except Exception as e:
            _LOGGER.error(f"Error in battery planning: {str(e)}")
            return {}

    async def _async_update_data(self) -> Dict[str, Any]:
        """Update data."""
        return await self.get_plan()

    async def set_param(self, param: str, value) -> Any:
        """Set parameter value."""
        if param not in self._params:
            raise ValueError(f"Invalid parameter: {param}")
        self._params[param] = value
        return value

    async def get_param_value(self, param: str) -> Any:
        """Get parameter value."""
        if param not in self._params:
            raise ValueError(f"Invalid parameter: {param}")
        return self._params[param]