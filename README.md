# Stenite Battery Planner Integration

This custom integration for Home Assistant connects to the Stenite Battery Planner API to optimize battery charging and discharging schedules based on electricity prices from Nordpool.

## Features

- Optimizes battery charging/discharging based on real-time electricity prices
- Supports all Nordpool SE price areas (SE1-SE4)
- Configurable battery parameters (capacity, charge/discharge rates, SOC limits)
- Takes into account battery degradation costs and grid tariffs
- Provides both immediate power recommendations and 24-hour schedules
- Creates input entities for all configuration parameters

## Installat    ion

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots in the top right corner
3. Select "Custom repositories"
4. Add this repository URL: `https://github.com/stenite/ha-battery-planner`
5. Select category: "Integration"
6. Click "Add"
7. Install the "Stenite Battery Planner" integration

### Manual Installation

1. Download the latest release from `https://github.com/stenite/ha-battery-planner`
2. Copy the `custom_components/stenite_battery_planner` directory to your Home Assistant's `custom_components` directory
3. Restart Home Assistant

## Configuration

Add the following to your `configuration.yaml`:

```yaml
stenite_battery_planner:
  name: "Battery Planner"  # Optional, defaults to "Battery Planner"
```

## Available Services

### stenite_battery_planner.plan

Creates an optimized battery charging/discharging schedule.

#### Service Data

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| nordpool_area | string | Yes | Nordpool price area (SE1-SE4) | - |
| mean_draw | float | Yes | Average power consumption (kW) | - |
| battery_capacity | float | Yes | Total battery capacity (kWh) | - |
| battery_min_soc | float | Yes | Minimum state of charge (%) | - |
| battery_max_soc | float | Yes | Maximum state of charge (%) | - |
| battery_soc | float | Yes | Current state of charge (%) | - |
| battery_max_discharge | float | Yes | Maximum discharge power (kW) | - |
| battery_min_discharge | float | Yes | Minimum discharge power (kW) | - |
| battery_max_charge | float | Yes | Maximum charge power (kW) | - |
| battery_min_charge | float | Yes | Minimum charge power (kW) | - |
| battery_allow_export | boolean | Yes | Allow battery to export to grid | false |
| battery_cycle_cost | float | Yes | Cost per full battery cycle | - |
| network_charge_kWh | float | Yes | Grid tariff per kWh | - |

#### Response

The service returns a JSON object containing:

```json
{
  "watts": 1000,  // Immediate power setting (positive=charge, negative=discharge)
  "action_type": "charge",  // Current action (charge/discharge/idle/self_consumption)
  "search_time": 0.5,  // Time taken to calculate solution
  "total_cost": 100.0,  // Total cost with optimization
  "baseline_cost": 150.0,  // Cost without optimization
  "status": "success",  // Status of optimization
  "schedule": [  // 24-hour schedule
    {
      "time": "2024-01-01T00:00:00Z",
      "price": 0.5,
      "cost": 2.5,
      "starting_soc": 0.5,
      "ending_soc": 0.6,
      "action_type": "charge",
      "watts": 1000
    }
  ]
}
```

## Example Automation

```yaml
alias: "Daily Battery Planning"
description: "Plans battery charging/discharging based on electricity prices"
trigger:
  - platform: time
    at: "00:00:00"
action:
  - service: stenite_battery_planner.plan
    data:
      nordpool_area: "SE3"
      mean_draw: 1.5
      battery_capacity: 10.0
      battery_min_soc: 20
      battery_max_soc: 90
      battery_soc: 50
      battery_max_discharge: 3.0
      battery_min_discharge: 0.1
      battery_max_charge: 3.0
      battery_min_charge: 0.1
      battery_allow_export: false
      battery_cycle_cost: 0.5
      network_charge_kWh: 0.25
```

## Entities Created

The integration creates the following entities:

### Number Entities
- Battery Capacity (kWh)
- Maximum/Minimum State of Charge (%)
- Current State of Charge (%)
- Maximum/Minimum Charge Power (kW)
- Maximum/Minimum Discharge Power (kW)
- Battery Cycle Cost
- Grid Import Cost
- Mean Power Consumption (kW)

### Select Entities
- Nordpool Area (SE1-SE4)
- Allow Grid Export (True/False)

## Debugging

If you encounter issues:

1. Enable debug logging by adding to `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.stenite_battery_planner: debug
```

2. Check the Home Assistant logs for any error messages
3. Verify all required parameters are within valid ranges
4. Ensure your battery parameters are consistent (e.g., min_soc < max_soc)

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) first.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For bug reports and feature requests, please [open an issue](https://github.com/stenite/ha-battery-planner/issues) on GitHub.