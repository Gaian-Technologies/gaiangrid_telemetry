# gaiangrid_telemetry

`gaiangrid_telemetry` is the Gaian Grid Home Assistant custom integration.

It is the project-specific layer on top of the generic
[`ha_telemetry`](/ssd2/Gaian/Workspace/ha_telemetry) workflow.

The supported setup path is:

1. install the integration in Home Assistant
2. request an enrollment token from `https://gaiangrid.com/enroll`
3. enter the enrollment token
4. select the supported electricity sensors to share
5. Home Assistant enrolls against `https://gaiangrid.com`
6. Gaian Grid returns broker credentials and topic details
7. Home Assistant connects directly to the MQTT broker over TLS

The repo root is the install path for Home Assistant. Clone it directly into:

    /config/custom_components/gaiangrid_telemetry

## Install

1. Clone the repo.

   ```bash
   cd /config/custom_components
   git clone <repo-url> gaiangrid_telemetry
   ```

2. Restart Home Assistant.

## Supported Setup

This integration is fixed to the Gaian Grid public Hub URL:

- `https://gaiangrid.com`

The setup flow asks only for:

- Enrollment token
- Gaian Grid electricity sensors
- Fallback telemetry interval
- Fallback heartbeat interval

## Supported Sensors

Gaian Grid currently accepts only electricity sensors with these units:

- voltage: `V`
- frequency: `Hz`
- reactive power: `var`
- real power: `W`

That means the initial integration selection is intentionally narrow. The
target use case is grid-relevant electricity telemetry such as voltage,
frequency, and real or reactive power measurements.

## Notes

- The public Hub URL is fixed in code for this project-specific integration.
- This integration supports managed Gaian Grid enrollment only.
- If setup says it cannot reach Gaian Grid, check public reachability to
  `https://gaiangrid.com`.
- If setup says it cannot connect to the MQTT broker returned by the hub, check
  public reachability to port `8883`, TLS certificate validity, and the broker
  hostname returned by the hub.
