from __future__ import annotations

from typing import Final

DOMAIN: Final = "gaiangrid_telemetry"

CONF_HUB_URL: Final = "hub_url"
CONF_ENROLLMENT_TOKEN: Final = "enrollment_token"
CONF_SITE_ID: Final = "site_id"
CONF_TOPIC_PREFIX: Final = "topic_prefix"
CONF_MQTT_USERNAME: Final = "mqtt_username"
CONF_MQTT_PASSWORD: Final = "mqtt_password"
CONF_ENTITY_IDS: Final = "entity_ids"
CONF_GRID_VOLTAGE_ENTITY_IDS: Final = "grid_voltage_entity_ids"
CONF_GRID_FREQUENCY_ENTITY_IDS: Final = "grid_frequency_entity_ids"
CONF_GRID_NET_POWER_ENTITY_IDS: Final = "grid_net_power_entity_ids"
CONF_GRID_IMPORT_POWER_ENTITY_IDS: Final = "grid_import_power_entity_ids"
CONF_GRID_EXPORT_POWER_ENTITY_IDS: Final = "grid_export_power_entity_ids"
CONF_ADDITIONAL_POWER_ENTITY_IDS: Final = "additional_power_entity_ids"
CONF_REACTIVE_POWER_ENTITY_IDS: Final = "reactive_power_entity_ids"
CONF_TELEMETRY_INTERVAL_SECONDS: Final = "telemetry_interval_seconds"
CONF_HEARTBEAT_INTERVAL_SECONDS: Final = "heartbeat_interval_seconds"

TRANSPORT_TCP: Final = "tcp"

SIGNAL_ROLE_GRID_VOLTAGE: Final = "grid_voltage"
SIGNAL_ROLE_GRID_FREQUENCY: Final = "grid_frequency"
SIGNAL_ROLE_GRID_POWER_NET: Final = "grid_power_net"
SIGNAL_ROLE_GRID_POWER_IMPORT: Final = "grid_power_import"
SIGNAL_ROLE_GRID_POWER_EXPORT: Final = "grid_power_export"
SIGNAL_ROLE_POWER_AUX: Final = "power_aux"
SIGNAL_ROLE_REACTIVE_POWER: Final = "reactive_power"
ATTR_GAIAN_SIGNAL_ROLE: Final = "gaian_signal_role"

DEFAULT_TOPIC_PREFIX: Final = "ha_telemetry/v1"
DEFAULT_PORT: Final = 8883
DEFAULT_TELEMETRY_INTERVAL_SECONDS: Final = 30
DEFAULT_HEARTBEAT_INTERVAL_SECONDS: Final = 60
FIXED_HUB_URL: Final = "https://gaiangrid.com"

TELEMETRY_ATTRIBUTE_ALLOWLIST: Final[tuple[str, ...]] = (
    "device_class",
    "friendly_name",
    "icon",
    "state_class",
    "unit_of_measurement",
)

ENTITY_ROLE_TO_CONFIG_KEY: Final[dict[str, str]] = {
    SIGNAL_ROLE_GRID_VOLTAGE: CONF_GRID_VOLTAGE_ENTITY_IDS,
    SIGNAL_ROLE_GRID_FREQUENCY: CONF_GRID_FREQUENCY_ENTITY_IDS,
    SIGNAL_ROLE_GRID_POWER_NET: CONF_GRID_NET_POWER_ENTITY_IDS,
    SIGNAL_ROLE_GRID_POWER_IMPORT: CONF_GRID_IMPORT_POWER_ENTITY_IDS,
    SIGNAL_ROLE_GRID_POWER_EXPORT: CONF_GRID_EXPORT_POWER_ENTITY_IDS,
    SIGNAL_ROLE_POWER_AUX: CONF_ADDITIONAL_POWER_ENTITY_IDS,
    SIGNAL_ROLE_REACTIVE_POWER: CONF_REACTIVE_POWER_ENTITY_IDS,
}

ENTITY_SELECTION_CONFIG_KEYS: Final[tuple[str, ...]] = tuple(ENTITY_ROLE_TO_CONFIG_KEY.values())
