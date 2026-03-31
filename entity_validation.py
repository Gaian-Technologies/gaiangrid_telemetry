"""Gaian Grid entity selection rules."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from .const import (
    CONF_ADDITIONAL_POWER_ENTITY_IDS,
    CONF_ADDITIONAL_FREQUENCY_ENTITY_IDS,
    CONF_ADDITIONAL_VOLTAGE_ENTITY_IDS,
    CONF_BATTERY_CHARGE_POWER_ENTITY_IDS,
    CONF_BATTERY_DISCHARGE_POWER_ENTITY_IDS,
    CONF_BATTERY_NET_POWER_ENTITY_IDS,
    CONF_GRID_EXPORT_POWER_ENTITY_IDS,
    CONF_GRID_FREQUENCY_ENTITY_IDS,
    CONF_GRID_IMPORT_POWER_ENTITY_IDS,
    CONF_GRID_NET_POWER_ENTITY_IDS,
    CONF_GRID_VOLTAGE_ENTITY_IDS,
    CONF_REACTIVE_POWER_ENTITY_IDS,
)


EXPECTED_UNIT_BY_FIELD: dict[str, tuple[str, str]] = {
    CONF_GRID_VOLTAGE_ENTITY_IDS: ("V", "unsupported_pcc_voltage_selection"),
    CONF_ADDITIONAL_VOLTAGE_ENTITY_IDS: ("V", "unsupported_additional_voltage_selection"),
    CONF_GRID_FREQUENCY_ENTITY_IDS: ("Hz", "unsupported_pcc_frequency_selection"),
    CONF_ADDITIONAL_FREQUENCY_ENTITY_IDS: ("Hz", "unsupported_additional_frequency_selection"),
    CONF_GRID_NET_POWER_ENTITY_IDS: ("W", "unsupported_pcc_power_selection"),
    CONF_GRID_IMPORT_POWER_ENTITY_IDS: ("W", "unsupported_pcc_power_selection"),
    CONF_GRID_EXPORT_POWER_ENTITY_IDS: ("W", "unsupported_pcc_power_selection"),
    CONF_ADDITIONAL_POWER_ENTITY_IDS: ("W", "unsupported_additional_power_selection"),
    CONF_BATTERY_NET_POWER_ENTITY_IDS: ("W", "unsupported_battery_power_selection"),
    CONF_BATTERY_CHARGE_POWER_ENTITY_IDS: ("W", "unsupported_battery_power_selection"),
    CONF_BATTERY_DISCHARGE_POWER_ENTITY_IDS: ("W", "unsupported_battery_power_selection"),
    CONF_REACTIVE_POWER_ENTITY_IDS: ("var", "unsupported_reactive_power_selection"),
}


def validate_selected_entities(
    hass: HomeAssistant,
    selections: dict[str, tuple[str, ...]],
) -> str | None:
    """Require the expected sensor unit for each explicit Gaian Grid field."""

    for key, (expected_unit, error_key) in EXPECTED_UNIT_BY_FIELD.items():
        for entity_id in selections.get(key, ()):
            if not entity_id.startswith("sensor."):
                return error_key

            state = hass.states.get(entity_id)
            if state is None:
                return error_key

            unit = str(state.attributes.get("unit_of_measurement", "")).strip()
            if unit != expected_unit:
                return error_key

    return None
