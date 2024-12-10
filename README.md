# Stenite Battery Planner Integration for Home Assistant

This integration allows you to optimize your battery storage system based on Nordpool electricity prices. It provides recommendations for when to charge and discharge your battery to minimize electricity costs while maintaining your desired battery parameters.

## Features

- Real-time battery charge/discharge recommendations based on Nordpool prices
- Configurable battery parameters (capacity, SOC limits, charge/discharge rates)
- Support for different Nordpool price areas (SE1-SE4)
- Cost optimization considering battery cycle costs and network charges
- Automatic updates every 5 minutes
- Export-to-grid configuration options

## Installation

### HACS Installation (Recommended)
1. Install [HACS](https://hacs.xyz/) if you haven't already
2. Go to HACS → Integrations → "+ Explore & Download Repositories"
3. Search for "Stenite Battery Planner"
4. Click Install
5. Restart Home Assistant

### Manual Installation
1. Copy the `stenite_battery_planner` directory to your `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to Settings → Devices & Services
2. Click "+ Add Integration"
3. Search for "Stenite Battery Planner"
4. Fill in the configuration form:

### Configuration Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| Name | Name of the integration instance | Battery Planner |
| Nordpool Area | Your Nordpool price area (SE1-SE4) | SE3 |
| Mean Power Draw | Average power consumption in kW | 2.0 |
| Battery Capacity | Total battery capacity in kWh | 10.0 |
| Battery Min SOC | Minimum state of charge (%) | 20 |
| Battery Max SOC | Maximum state of charge (%) | 80 |
| Battery Min Discharge | Minimum discharge power in kW | 0.0 |
| Battery Max Discharge | Maximum discharge power in kW | 1.0 |
| Battery Min Charge | Minimum charge power in kW | 0.0 |
| Battery Max Charge | Maximum charge power in kW | 1.0 |
| Battery SOC | Current battery state of charge (%) | 50 |
| Battery Cycle Cost | Cost of one full battery cycle | 0.3 |
| Allow Battery Export | Allow exporting to grid | true |
| Network Charge | Grid utility import cost per kWh | 0.3 |

## Entities Created

### Sensors

1. **Current Recommended Action**
   - Shows the recommended battery action (charge/discharge/idle/self_consumption)
   - Entity ID: `sensor.battery_planner_current_recommended_action`

2. **Current Recommended Power**
   - Shows the recommended power level in watts
   - Entity ID: `sensor.battery_planner_current_recommended_power`
   - Device class: power
   - State class: measurement

3. **Expected Savings**
   - Shows the expected cost savings
   - Entity ID: `sensor.battery_planner_expected_savings`
   - Attributes:
     - baseline_cost: Cost without optimization
     - total_cost: Cost with optimization

### Number Entities

The integration creates number entities for all configurable parameters, allowing you to adjust settings through the Home Assistant interface.

### Select Entities

- Nordpool Area selector (SE1-SE4)
- Battery Export toggle

## Services

The integration provides a `stenite_battery_planner.plan` service that allows you to trigger planning calculations with custom parameters:

```yaml
service: stenite_battery_planner.plan
data:
  nordpool_area: "SE3"
  mean_draw: 2.0
  battery_capacity: 10.0
  battery_min_soc: 20
  battery_max_soc: 80
  battery_min_discharge: 0.0
  battery_max_discharge: 1.0
  battery_min_charge: 0.0
  battery_max_charge: 1.0
  battery_soc: 50
  battery_cycle_cost: 0.3
  battery_allow_export: true
  network_charge_kWh: 0.3
```

## API Endpoints

The integration communicates with the Stenite Battery Planner API at:
- Planning endpoint: `https://batteryplanner.stenite.com/api/v2.0/plan`

## Error Handling

The integration includes validation for:
- SOC limits (min cannot exceed max)
- Charge/discharge power limits
- Parameter ranges and types
- API communication errors

## Troubleshooting

1. Check the Home Assistant logs for any error messages
2. Verify your Nordpool area setting
3. Ensure all battery parameters are within valid ranges
4. Check your network connectivity to the Stenite API

## Contributing

Feel free to submit issues and pull requests on the GitHub repository.

## License

This project is licensed under MIT License - see the LICENSE file for details.