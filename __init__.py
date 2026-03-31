from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from .const import (
    CONF_ENTITY_IDS,
    CONF_GRID_NET_POWER_SIGN_CONVENTION,
    DEFAULT_GRID_NET_POWER_SIGN_CONVENTION,
    DOMAIN,
    ENTITY_SELECTION_CONFIG_KEYS,
)
from .manager import TelemetryManager
from .models import EntrySettings, classify_legacy_entity_ids
from .mqtt_client import MqttAuthenticationError, MqttConnectionError


async def async_setup(hass: HomeAssistant, _config: dict) -> bool:
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if entry.version >= 4:
        return True

    migrated_data = dict(entry.data)
    migrated_options = dict(entry.options)

    for payload in (migrated_data, migrated_options):
        legacy_entity_ids = payload.pop(CONF_ENTITY_IDS, [])
        if legacy_entity_ids:
            payload.update(classify_legacy_entity_ids(hass, legacy_entity_ids))
        payload.pop("battery_net_power_entity_ids", None)
        payload.pop("battery_net_power_sign_convention", None)
        payload.pop("battery_charge_power_entity_ids", None)
        payload.pop("battery_discharge_power_entity_ids", None)
        payload.pop("reactive_power_entity_ids", None)
        for key in ENTITY_SELECTION_CONFIG_KEYS:
            payload.setdefault(key, [])
        payload.setdefault(
            CONF_GRID_NET_POWER_SIGN_CONVENTION,
            DEFAULT_GRID_NET_POWER_SIGN_CONVENTION,
        )

    hass.config_entries.async_update_entry(
        entry,
        data=migrated_data,
        options=migrated_options,
        version=4,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    settings = EntrySettings.from_entry(hass, entry)
    manager = TelemetryManager(hass, entry, settings)

    try:
        await manager.async_start()
    except MqttAuthenticationError as err:
        raise ConfigEntryAuthFailed(f"Failed to authenticate MQTT client for {settings.site_id}") from err
    except MqttConnectionError as err:
        raise ConfigEntryNotReady(f"Failed to initialize MQTT client for {settings.site_id}") from err
    except Exception as err:
        raise ConfigEntryNotReady(f"Failed to initialize MQTT client for {settings.site_id}") from err

    hass.data[DOMAIN][entry.entry_id] = manager
    entry.runtime_data = manager
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    manager: TelemetryManager = hass.data[DOMAIN].pop(entry.entry_id)
    await manager.async_stop()
    entry.runtime_data = None
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
