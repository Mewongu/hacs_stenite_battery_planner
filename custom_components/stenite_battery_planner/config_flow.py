"""Config flow for Stenite Battery Planner."""
from __future__ import annotations

import logging
import voluptuous as vol
from typing import Any

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.core import callback
from homeassistant.helpers import selector

from . import (
    DOMAIN,
    DEFAULT_NAME,
    validate_positive_float,
    validate_positive_or_zero_float,
    validate_percentage,
)

_LOGGER = logging.getLogger(__name__)

NORDPOOL_AREAS = ["SE1", "SE2", "SE3", "SE4"]

class SteniteBatteryPlannerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Stenite Battery Planner."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                # Generate a unique ID based on the name
                unique_id = f"{DOMAIN}_{user_input[CONF_NAME]}"

                # Check if this specific instance is already configured
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                # Validate interdependent values
                if user_input.get("battery_min_soc", 0) > user_input.get("battery_max_soc", 100):
                    errors["battery_min_soc"] = "min_soc_exceeds_max"
                if user_input.get("battery_min_discharge", 0) > user_input.get("battery_max_discharge", 1):
                    errors["battery_min_discharge"] = "min_discharge_exceeds_max"
                if user_input.get("battery_min_charge", 0) > user_input.get("battery_max_charge", 1):
                    errors["battery_min_charge"] = "min_charge_exceeds_max"

                if not errors:
                    return self.async_create_entry(
                        title=user_input[CONF_NAME],
                        data=user_input
                    )

            except Exception as error:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # Define the schema using selectors for better control
        data_schema = {
            vol.Required(CONF_NAME, default=DEFAULT_NAME): selector.TextSelector(),
            vol.Required("nordpool_area", default="SE3"): selector.SelectSelector(
                selector.SelectSelectorConfig(options=NORDPOOL_AREAS)
            ),
            vol.Required("mean_draw", default=2.0): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100, step=0.001, mode="box")
            ),
            vol.Required("battery_capacity", default=10.0): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=1000, step=0.001, mode="box")
            ),
            vol.Required("battery_min_soc", default=20): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100, step=1, mode="box")
            ),
            vol.Required("battery_max_soc", default=80): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100, step=1, mode="box")
            ),
            vol.Required("battery_min_discharge", default=0.0): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100, step=0.001, mode="box")
            ),
            vol.Required("battery_max_discharge", default=1.0): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100, step=0.001, mode="box")
            ),
            vol.Required("battery_min_charge", default=0.0): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100, step=0.001, mode="box")
            ),
            vol.Required("battery_max_charge", default=1.0): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100, step=0.001, mode="box")
            ),
            vol.Required("battery_soc", default=50): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100, step=0.01, mode="box")
            ),
            vol.Required("battery_cycle_cost", default=0.3): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100, step=0.001, mode="box")
            ),
            vol.Required("battery_allow_export", default=True): selector.BooleanSelector(),
            vol.Required("network_charge_kWh", default=0.3): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100, step=0.01, mode="box")
            ),
            vol.Required("stored_value_per_kWh", default=0.0): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100, step=0.01, mode="box")
            ),
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(data_schema),
            errors=errors,
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for the integration."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage options."""
        errors = {}

        if user_input is not None:
            try:
                # Validate interdependent values
                if user_input.get("battery_min_soc", 0) > user_input.get("battery_max_soc", 100):
                    errors["battery_min_soc"] = "min_soc_exceeds_max"
                if user_input.get("battery_min_discharge", 0) > user_input.get("battery_max_discharge", 1):
                    errors["battery_min_discharge"] = "min_discharge_exceeds_max"
                if user_input.get("battery_min_charge", 0) > user_input.get("battery_max_charge", 1):
                    errors["battery_min_charge"] = "min_charge_exceeds_max"

                if not errors:
                    # Update the config entry data with the new values
                    new_data = dict(self.config_entry.data)
                    new_data.update(user_input)

                    self.hass.config_entries.async_update_entry(
                        self.config_entry,
                        data=new_data,
                    )

                    # Update coordinator parameters if available
                    coordinator = self.hass.data[DOMAIN].get(self.config_entry.entry_id)
                    if coordinator:
                        for key, value in user_input.items():
                            await coordinator.set_param(key, value)
                        await coordinator.async_refresh()

                    return self.async_create_entry(title="", data=user_input)
            except Exception as error:
                errors["base"] = "unknown"

        # Get current values from config entry
        current = {
            "nordpool_area": self.config_entry.data.get("nordpool_area", "SE3"),
            "mean_draw": self.config_entry.data.get("mean_draw", 2.0),
            "battery_capacity": self.config_entry.data.get("battery_capacity", 10.0),
            "battery_min_soc": self.config_entry.data.get("battery_min_soc", 20),
            "battery_max_soc": self.config_entry.data.get("battery_max_soc", 80),
            "battery_min_discharge": self.config_entry.data.get("battery_min_discharge", 0.0),
            "battery_max_discharge": self.config_entry.data.get("battery_max_discharge", 1.0),
            "battery_min_charge": self.config_entry.data.get("battery_min_charge", 0.0),
            "battery_max_charge": self.config_entry.data.get("battery_max_charge", 1.0),
            "battery_soc": self.config_entry.data.get("battery_soc", 50),
            "battery_cycle_cost": self.config_entry.data.get("battery_cycle_cost", 0.3),
            "battery_allow_export": self.config_entry.data.get("battery_allow_export", True),
            "network_charge_kWh": self.config_entry.data.get("network_charge_kWh", 0.3),
            "stored_value_per_kWh": self.config_entry.data.get("stored_value_per_kWh", 0),
        }

        # Define schema using selectors
        data_schema = {
            vol.Required("nordpool_area", default=current["nordpool_area"]): selector.SelectSelector(
                selector.SelectSelectorConfig(options=NORDPOOL_AREAS)
            ),
            vol.Required("mean_draw", default=current["mean_draw"]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100, step=0.001, mode="box")
            ),
            vol.Required("battery_capacity", default=current["battery_capacity"]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=1000, step=0.001, mode="box")
            ),
            vol.Required("battery_min_soc", default=current["battery_min_soc"]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100, step=1, mode="box")
            ),
            vol.Required("battery_max_soc", default=current["battery_max_soc"]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100, step=1, mode="box")
            ),
            vol.Required("battery_min_discharge", default=current["battery_min_discharge"]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100, step=0.001, mode="box")
            ),
            vol.Required("battery_max_discharge", default=current["battery_max_discharge"]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100, step=0.001, mode="box")
            ),
            vol.Required("battery_min_charge", default=current["battery_min_charge"]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100, step=0.001, mode="box")
            ),
            vol.Required("battery_max_charge", default=current["battery_max_charge"]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100, step=0.001, mode="box")
            ),
            vol.Required("battery_soc", default=current["battery_soc"]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100, step=0.01, mode="box")
            ),
            vol.Required("battery_cycle_cost", default=current["battery_cycle_cost"]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100, step=0.001, mode="box")
            ),
            vol.Required("battery_allow_export", default=current["battery_allow_export"]): selector.BooleanSelector(),
            vol.Required("network_charge_kWh", default=current["network_charge_kWh"]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100, step=0.001, mode="box")
            ),vol.Required("stored_value_per_kWh", default=current["stored_value_per_kWh"]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100, step=0.001, mode="box")
            ),
        }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(data_schema),
            errors=errors,
        )