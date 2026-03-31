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
- PCC sensors if you have them
- Additional voltage sensors if you have smart plugs or outlet monitors
- Additional frequency sensors if you have smart plugs or outlet monitors
- PCC power sensors if you have inverter or main-switchboard measurements
- Additional downstream power sensors if they are useful to share
- Fallback telemetry interval
- Fallback heartbeat interval

In electric power distribution, the point of common coupling (PCC) is where a
consumer's electrical circuit connects to the utility grid.

For many grid-tied inverters, inverter voltage and inverter frequency are PCC
measurements. For CTs or a meter at the main switchboard, the switchboard-side
measurements are usually the PCC measurements. Smart plugs on outlets do not
qualify as PCC voltage or PCC frequency, but they can still be shared in the
additional voltage, additional frequency, and additional power fields where
useful.

## Supported Setup

This integration is fixed to the Gaian Grid public Hub URL:

- `https://gaiangrid.com`

The setup flow asks only for:

- the enrollment token
- the selected electricity sensors
- the fallback telemetry interval
- the fallback heartbeat interval

If you have PCC voltage, PCC frequency, or PCC power sensors, those are the
preferred inputs and you do not need anything else. If you do not have PCC
sensors, even a single voltage, frequency, or device power sensor is still
helpful.

## Supported Sensors

Gaian Grid currently accepts electricity sensors in these roles:

- PCC voltage sensors: `V`
- additional voltage sensors: `V`
- PCC frequency sensors: `Hz`
- additional frequency sensors: `Hz`
- PCC net power sensors: `W`
  - choose the sign convention in the setup form so Gaian Grid knows whether
    import is reported as positive or negative
- PCC import power sensors: `W`
- PCC export power sensors: `W`
- additional electricity power sensors: `W`

PCC power is the preferred input for Gaian Grid Telemetry. If you do
not have PCC power sensors, additional electricity power sensors are still useful.

Do not select duplicate sensors for the same PCC measurement. If you already
have separate PCC import and export sensors, use those instead of also
selecting a PCC net power sensor.

## Notes

- The public Hub URL is fixed in code for this project-specific integration.
- This integration supports managed Gaian Grid enrollment only.
- A bundled `brand/icon.png` is included so recent Home Assistant versions can show the custom integration icon for both manual installs and HACS installs.
- If setup says it cannot reach Gaian Grid, check public reachability to
  `https://gaiangrid.com`.
- If setup says it cannot connect to the MQTT broker returned by the hub, check
  public reachability to port `8883`, TLS certificate validity, and the broker
  hostname returned by the hub.
