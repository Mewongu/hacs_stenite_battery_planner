# custom_components/stenite_battery_planner/__init__.py
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
import aiohttp

from homeassistant.core import HomeAssistant, SupportsResponse
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

DOMAIN = "stenite_battery_planner"
_LOGGER = logging.getLogger(__name__)

# Default endpoint
DEFAULT_ENDPOINT = "http://10.1.1.111:5050/"

# Configuration schema
CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional('endpoint', default=DEFAULT_ENDPOINT): cv.url,
    })
}, extra=vol.ALLOW_EXTRA)

# Service call schema
CALL_SERVICE_SCHEMA = vol.Schema({
    vol.Required('state_of_charge'): vol.Coerce(float),
    vol.Optional('endpoint'): cv.url,
})

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Stenite Battery Planner Integration."""
    conf = config.get(DOMAIN, {})
    default_endpoint = conf.get('endpoint', DEFAULT_ENDPOINT)
    
    async def plan_battery(call):
        """Handle the battery planning service call."""
        # Get state of charge from service call
        state_of_charge = call.data['state_of_charge']
        
        # Use provided endpoint or fall back to default
        endpoint = call.data.get('endpoint', default_endpoint)
        
        # Prepare payload
        payload = {
            "state_of_charge": state_of_charge
        }
        
        try:
            session = async_get_clientsession(hass)
            async with session.post(endpoint, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    _LOGGER.info(f"Battery planning successful: {result}")
                    
                    # Fire an event with the planning result
                    hass.bus.async_fire(f"{DOMAIN}_plan_result", result)
                    
                    return result
                else:
                    error_text = await response.text()
                    _LOGGER.error(f"Battery planning failed with status {response.status}: {error_text}")
                    return None
        except Exception as e:
            _LOGGER.error(f"Error in battery planning: {e}")
            return None

    # Register the service
    hass.services.async_register(
        DOMAIN, 
        'plan', 
        plan_battery, 
        schema=CALL_SERVICE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    
    return True