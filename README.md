# Stenite Battery Planner Integration for Home Assistant

## Overview
This integration provides a battery planning service and sensor in Home Assistant, allowing detailed battery optimization planning.

## Installation
1. Copy the `stenite_battery_planner` folder to your Home Assistant `custom_components` directory.
2. Restart Home Assistant.

## Usage
### Triggering a Plan
Call the service with comprehensive battery and electricity details:

```yaml
service: stenite_battery_planner.plan
data:
  endpoint: http://10.1.1.111:5050/plan
  nordpool_area: "SE3"
  mean_draw: 2500
  battery_capacity: 17880
  min_battery_soc: 20.0
  max_battery_soc: 90.0
  max_battery_discharge: 5000
  max_battery_charge: 5000
  battery_soc: 75.5
  battery_allow_export: true
  seconds_to_search: 60
  cycle_cost: 0.3
```

### Parameters
- `endpoint`: URL of the planning service (required)
- `nordpool_area`: Nordpool electricity area (required)
- `mean_draw`: Average house power draw in kWh (required)
- `battery_capacity`: Total battery capacity in kWh (required)
- `min_battery_soc`: Minimum allowed battery state of charge (required)
- `max_battery_soc`: Maximum allowed battery state of charge (required)
- `battery_soc`: Current battery state of charge (required)
- `battery_allow_export`: Allow exporting to grid (optional, default: false)
- `seconds_to_search`: Optimization search time (optional, default: 60)

### Example Automation
```yaml
automation:
- alias: "Update Battery Plan Hourly"
  trigger:
    - platform: time_pattern
      hours: "/5"
  action:
    - service: stenite_battery_planner.plan
      data:
        endpoint: http://10.1.1.111:5050/
        nordpool_area: "{{ states('sensor.nordpool_area') }}"
        mean_draw: "{{ states('sensor.house_power_draw') }}"
        battery_capacity: "{{ states('sensor.battery_total_capacity') }}"
        min_battery_soc: 20.0
        max_battery_soc: 90.0
        max_battery_discharge: 5000
        max_battery_charge: 5000
        battery_soc: "{{ states('sensor.battery_state_of_charge') }}"
        battery_allow_export: true
        cycle_cost: 0.3
```

## Sensor Attributes
The sensor will provide detailed planning information from the service.