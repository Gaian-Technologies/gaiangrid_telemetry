"""Gaian Grid entity selection rules."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

SUPPORTED_UNITS: frozenset[str] = frozenset({"V", "Hz", "var", "W"})


def validate_selected_entities(hass: HomeAssistant, entity_ids: tuple[str, ...]) -> str | None:
    """Require electricity sensors with Gaian Grid's supported units."""

    for entity_id in entity_ids:
        if not entity_id.startswith("sensor."):
            return "unsupported_entity_selection"

        state = hass.states.get(entity_id)
        if state is None:
            return "unsupported_entity_selection"

        unit = str(state.attributes.get("unit_of_measurement", "")).strip()
        if unit not in SUPPORTED_UNITS:
            return "unsupported_entity_selection"

    return None
