# gaiangrid_telemetry

`gaiangrid_telemetry` is the Gaian Grid Home Assistant custom integration.

It is the project-specific layer on top of the generic
[`ha_telemetry`](https://github.com/Gaian-Technologies/ha_telemetry) workflow.

It is not the generic starting point for open-source adopters. If you want a
reusable integration for your own Hub deployment, start with
[`ha_telemetry`](/ssd2/Gaian/Workspace/ha_telemetry) instead.

The supported setup path is:

1. install the integration in Home Assistant
2. request an enrollment token from `https://gaiangrid.com/enroll`
3. enter the enrollment token
4. choose the supported electricity sensors to share
5. Home Assistant enrolls against `https://gaiangrid.com`
6. Gaian Grid returns broker credentials and topic details
7. Home Assistant connects directly to the MQTT broker over TLS

## Install

### Preferred: Manual Install

For early rollout, the simplest and most reproducible path is to place the
repo in:

    <config directory>/custom_components/gaiangrid_telemetry

The easiest manual path is usually the Home Assistant `Terminal & SSH`
add-on web terminal:

```bash
mkdir -p /config/custom_components
cd /config/custom_components
git clone https://github.com/Gaian-Technologies/gaiangrid_telemetry.git gaiangrid_telemetry
```

`mkdir -p` is safe to run even if `custom_components` already exists, so the
same command works for both first-time and experienced users.

On Home Assistant OS and Supervised installs, the configuration directory is
usually mounted at `/config`, so the commands above normally work as written.

If `/config` does not exist in your environment, first find your Home
Assistant configuration directory in:

`Settings -> System -> Repairs -> three dot menu -> System information`

Then create a `custom_components` directory inside that configuration
directory if needed, and place `gaiangrid_telemetry` there.

You can also download the GitHub ZIP and copy the extracted
`gaiangrid_telemetry` folder into `<config directory>/custom_components/` using
`Studio Code Server`, `File editor`, Samba, or another file access method.

Restart Home Assistant after installing or updating the integration. The most
generic path is the Home Assistant UI restart option. If you are using the
Home Assistant CLI in `Terminal & SSH`, run:

```bash
ha core restart
```

If your environment does not provide the `ha` command, reboot the host
instead:

```bash
reboot
```

If your shell is not already running as root, use `sudo reboot`.

### Optional: HACS Custom Repository

If you already use HACS, you can install this repo as a custom repository
instead.

1. Make sure HACS is already installed in Home Assistant.
2. Open `HACS`.
3. Open the top-right 3 dot menu, choose `Custom repositories`, and add:

   - Repository: `https://github.com/Gaian-Technologies/gaiangrid_telemetry`
   - Category: `Integration`

4. Find `Gaian Grid Telemetry` in HACS and download it.
5. Restart Home Assistant.

## Add The Integration

After Home Assistant has restarted:

1. Open `Settings`.
2. Open `Devices & Services`.
3. Open the `Integrations` tab.
4. Click `Add Integration`.
5. Search for `Gaian Grid Telemetry`.
6. Select the integration and continue through the setup form.

In the form, enter:

- Enrollment token
- Grid voltage sensors when available
- Grid frequency sensors when available
- Whole-grid power sensors if you have CTs or inverter/grid measurements
- Additional electricity power sensors if they are useful to share
- Fallback telemetry interval
- Fallback heartbeat interval

## Supported Setup

This integration is fixed to the Gaian Grid public Hub URL:

- `https://gaiangrid.com`

The setup flow asks only for:

- the enrollment token
- the selected electricity sensors
- the fallback telemetry interval
- the fallback heartbeat interval

Not all sensor fields are required. Whole-grid voltage, frequency, and power
are preferred if available, but even a single voltage measurement from a smart
plug helps.

## Supported Sensors

Gaian Grid currently accepts electricity sensors in these roles:

- grid voltage sensors: `V`
- grid frequency sensors: `Hz`
- whole-grid net power sensors: `W`
  - use these when positive means import and negative means export
- whole-grid import power sensors: `W`
- whole-grid export power sensors: `W`
- additional electricity power sensors: `W`
- reactive power sensors: `var`

Whole-grid power is the preferred input for Gaian Grid public summaries.
Additional electricity power sensors are still useful for research and future
analysis, but they are not treated as whole-grid import/export totals.

Do not select duplicate sensors for the same whole-grid measurement. If you
already have separate whole-grid import and export sensors, use those instead
of also selecting a whole-grid net power sensor.

## Notes

- The public Hub URL is fixed in code for this project-specific integration.
- This integration supports managed Gaian Grid enrollment only.
- A bundled `brand/icon.png` is included so recent Home Assistant versions can show the custom integration icon for both manual installs and HACS installs.
- If setup says it cannot reach Gaian Grid, check public reachability to
  `https://gaiangrid.com`.
- If setup says it cannot connect to the MQTT broker returned by the hub, check
  public reachability to port `8883`, TLS certificate validity, and the broker
  hostname returned by the hub.
