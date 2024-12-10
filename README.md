# Stenite Battery Planner Integration for Home Assistant

## Overview
This integration allows you to interact with the Stenite Battery Planner service to create battery plans based on the current state of charge.

## Installation
1. Copy the `stenite_battery_planner` folder to your Home Assistant `custom_components` directory.
2. Restart Home Assistant.

## Configuration
Optional configuration in `configuration.yaml`:

```yaml
stenite_battery_planner:
  endpoint: http://10.1.1.111:5050/
```

## Usage
Call the service in automations, scripts, or via the developer tools:

```yaml
service: stenite_battery_planner.plan
data:
  state_of_charge: 75.5
```

### Parameters
- `state_of_charge` (Required): Current battery state of charge as a percentage (0-100)
- `endpoint` (Optional): Alternative endpoint URL if different from default

## Events
The integration fires a `stenite_battery_planner_plan_result` event with the planning result when successful.