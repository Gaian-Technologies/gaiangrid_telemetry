"""Typed runtime models for the managed Home Assistant integration workflow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from .const import (
    CONF_ADDITIONAL_POWER_ENTITY_IDS,
    CONF_ENTITY_IDS,
    CONF_GRID_EXPORT_POWER_ENTITY_IDS,
    CONF_GRID_FREQUENCY_ENTITY_IDS,
    CONF_GRID_IMPORT_POWER_ENTITY_IDS,
    CONF_GRID_NET_POWER_ENTITY_IDS,
    CONF_GRID_VOLTAGE_ENTITY_IDS,
    CONF_HEARTBEAT_INTERVAL_SECONDS,
    CONF_HUB_URL,
    CONF_MQTT_PASSWORD,
    CONF_MQTT_USERNAME,
    CONF_REACTIVE_POWER_ENTITY_IDS,
    CONF_SITE_ID,
    CONF_TELEMETRY_INTERVAL_SECONDS,
    CONF_TOPIC_PREFIX,
    DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
    DEFAULT_PORT,
    DEFAULT_TELEMETRY_INTERVAL_SECONDS,
    DEFAULT_TOPIC_PREFIX,
    ENTITY_ROLE_TO_CONFIG_KEY,
    FIXED_HUB_URL,
    SIGNAL_ROLE_GRID_FREQUENCY,
    SIGNAL_ROLE_GRID_POWER_EXPORT,
    SIGNAL_ROLE_GRID_POWER_IMPORT,
    SIGNAL_ROLE_GRID_POWER_NET,
    SIGNAL_ROLE_GRID_VOLTAGE,
    SIGNAL_ROLE_POWER_AUX,
    SIGNAL_ROLE_REACTIVE_POWER,
    TRANSPORT_TCP,
)


def normalize_entity_ids(entity_ids: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(set(str(entity_id).strip() for entity_id in entity_ids if str(entity_id).strip())))


def _positive_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(1, parsed)


def classify_legacy_entity_ids(hass: HomeAssistant, entity_ids: list[str] | tuple[str, ...]) -> dict[str, list[str]]:
    selections: dict[str, list[str]] = {
        CONF_GRID_VOLTAGE_ENTITY_IDS: [],
        CONF_GRID_FREQUENCY_ENTITY_IDS: [],
        CONF_GRID_NET_POWER_ENTITY_IDS: [],
        CONF_GRID_IMPORT_POWER_ENTITY_IDS: [],
        CONF_GRID_EXPORT_POWER_ENTITY_IDS: [],
        CONF_ADDITIONAL_POWER_ENTITY_IDS: [],
        CONF_REACTIVE_POWER_ENTITY_IDS: [],
    }

    for entity_id in normalize_entity_ids(entity_ids):
        state = hass.states.get(entity_id)
        unit = str(state.attributes.get("unit_of_measurement", "")).strip() if state else ""
        if unit == "V":
            selections[CONF_GRID_VOLTAGE_ENTITY_IDS].append(entity_id)
        elif unit == "Hz":
            selections[CONF_GRID_FREQUENCY_ENTITY_IDS].append(entity_id)
        elif unit == "var":
            selections[CONF_REACTIVE_POWER_ENTITY_IDS].append(entity_id)
        elif unit == "W":
            # Legacy entries only had a single flat selector, so the least
            # surprising migration is to preserve existing Gaian Grid behavior
            # and treat historical W sensors as PCC net power inputs.
            selections[CONF_GRID_NET_POWER_ENTITY_IDS].append(entity_id)
    return selections


def _role_entity_ids(data: dict[str, Any], key: str) -> tuple[str, ...]:
    return normalize_entity_ids(data.get(key, []))


@dataclass(slots=True, frozen=True)
class TelemetrySelection:
    entity_id: str
    signal_role: str


@dataclass(slots=True, frozen=True)
class EntrySettings:
    """Resolved integration settings for one enrolled Home Assistant site."""

    hub_url: str
    host: str
    port: int
    site_id: str
    topic_prefix: str
    mqtt_username: str
    mqtt_password: str
    grid_voltage_entity_ids: tuple[str, ...]
    grid_frequency_entity_ids: tuple[str, ...]
    grid_net_power_entity_ids: tuple[str, ...]
    grid_import_power_entity_ids: tuple[str, ...]
    grid_export_power_entity_ids: tuple[str, ...]
    additional_power_entity_ids: tuple[str, ...]
    reactive_power_entity_ids: tuple[str, ...]
    telemetry_interval_seconds: int
    heartbeat_interval_seconds: int

    @property
    def transport(self) -> str:
        return TRANSPORT_TCP

    @property
    def selected_entities(self) -> tuple[TelemetrySelection, ...]:
        ordered: list[TelemetrySelection] = []
        for signal_role, entity_ids in (
            (SIGNAL_ROLE_GRID_VOLTAGE, self.grid_voltage_entity_ids),
            (SIGNAL_ROLE_GRID_FREQUENCY, self.grid_frequency_entity_ids),
            (SIGNAL_ROLE_GRID_POWER_NET, self.grid_net_power_entity_ids),
            (SIGNAL_ROLE_GRID_POWER_IMPORT, self.grid_import_power_entity_ids),
            (SIGNAL_ROLE_GRID_POWER_EXPORT, self.grid_export_power_entity_ids),
            (SIGNAL_ROLE_POWER_AUX, self.additional_power_entity_ids),
            (SIGNAL_ROLE_REACTIVE_POWER, self.reactive_power_entity_ids),
        ):
            ordered.extend(
                TelemetrySelection(entity_id=entity_id, signal_role=signal_role)
                for entity_id in entity_ids
            )
        return tuple(ordered)

    @property
    def all_entity_ids(self) -> tuple[str, ...]:
        return tuple(selection.entity_id for selection in self.selected_entities)

    @property
    def selected_entities_by_role(self) -> dict[str, list[str]]:
        return {
            signal_role: [
                selection.entity_id
                for selection in self.selected_entities
                if selection.signal_role == signal_role
            ]
            for signal_role in ENTITY_ROLE_TO_CONFIG_KEY
        }

    @classmethod
    def from_entry(cls, hass: HomeAssistant, entry: ConfigEntry) -> "EntrySettings":
        merged = dict(entry.data)
        merged.update(entry.options)
        return cls.from_mapping(hass, merged)

    @classmethod
    def from_mapping(cls, hass: HomeAssistant, data: dict[str, Any]) -> "EntrySettings":
        normalized_data = dict(data)
        if not any(key in normalized_data for key in ENTITY_ROLE_TO_CONFIG_KEY.values()):
            normalized_data.update(classify_legacy_entity_ids(hass, normalized_data.get(CONF_ENTITY_IDS, [])))

        return cls(
            hub_url=str(normalized_data.get(CONF_HUB_URL, FIXED_HUB_URL)).strip().rstrip("/"),
            host=str(normalized_data[CONF_HOST]).strip(),
            port=int(normalized_data.get(CONF_PORT, DEFAULT_PORT)),
            site_id=str(normalized_data[CONF_SITE_ID]).strip(),
            topic_prefix=str(normalized_data.get(CONF_TOPIC_PREFIX, DEFAULT_TOPIC_PREFIX)).strip("/"),
            mqtt_username=str(normalized_data[CONF_MQTT_USERNAME]).strip(),
            mqtt_password=str(normalized_data[CONF_MQTT_PASSWORD]),
            grid_voltage_entity_ids=_role_entity_ids(normalized_data, CONF_GRID_VOLTAGE_ENTITY_IDS),
            grid_frequency_entity_ids=_role_entity_ids(normalized_data, CONF_GRID_FREQUENCY_ENTITY_IDS),
            grid_net_power_entity_ids=_role_entity_ids(normalized_data, CONF_GRID_NET_POWER_ENTITY_IDS),
            grid_import_power_entity_ids=_role_entity_ids(normalized_data, CONF_GRID_IMPORT_POWER_ENTITY_IDS),
            grid_export_power_entity_ids=_role_entity_ids(normalized_data, CONF_GRID_EXPORT_POWER_ENTITY_IDS),
            additional_power_entity_ids=_role_entity_ids(normalized_data, CONF_ADDITIONAL_POWER_ENTITY_IDS),
            reactive_power_entity_ids=_role_entity_ids(normalized_data, CONF_REACTIVE_POWER_ENTITY_IDS),
            telemetry_interval_seconds=_positive_int(
                normalized_data.get(CONF_TELEMETRY_INTERVAL_SECONDS),
                DEFAULT_TELEMETRY_INTERVAL_SECONDS,
            ),
            heartbeat_interval_seconds=_positive_int(
                normalized_data.get(CONF_HEARTBEAT_INTERVAL_SECONDS),
                DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
            ),
        )


@dataclass(slots=True, frozen=True)
class ManagedEnrollmentResult:
    """Broker credentials and hub metadata returned by enrollment."""

    site_id: str
    mqtt_host: str
    mqtt_port: int
    mqtt_topic_prefix: str
    mqtt_username: str
    mqtt_password: str
    hub_url: str


@dataclass(slots=True)
class DesiredConfig:
    """Hub-controlled behavior that the integration applies locally."""

    enabled: bool
    telemetry_interval_seconds: int
    heartbeat_interval_seconds: int
    config_version: int

    @classmethod
    def from_settings(cls, settings: EntrySettings) -> "DesiredConfig":
        return cls(
            enabled=True,
            telemetry_interval_seconds=settings.telemetry_interval_seconds,
            heartbeat_interval_seconds=settings.heartbeat_interval_seconds,
            config_version=0,
        )

    @classmethod
    def from_payload(cls, payload: dict[str, Any], settings: EntrySettings) -> "DesiredConfig":
        return cls(
            enabled=bool(payload.get("enabled", True)),
            telemetry_interval_seconds=_positive_int(
                payload.get("telemetry_interval_seconds"),
                settings.telemetry_interval_seconds,
            ),
            heartbeat_interval_seconds=_positive_int(
                payload.get("heartbeat_interval_seconds"),
                settings.heartbeat_interval_seconds,
            ),
            config_version=int(payload.get("config_version", 0)),
        )
