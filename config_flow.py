"""Home Assistant config flow for the managed hub enrollment workflow."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers import selector

from .entity_validation import validate_selected_entities
from .const import (
    CONF_ADDITIONAL_POWER_ENTITY_IDS,
    CONF_ADDITIONAL_FREQUENCY_ENTITY_IDS,
    CONF_ADDITIONAL_VOLTAGE_ENTITY_IDS,
    CONF_ENROLLMENT_TOKEN,
    CONF_GRID_EXPORT_POWER_ENTITY_IDS,
    CONF_GRID_FREQUENCY_ENTITY_IDS,
    CONF_GRID_IMPORT_POWER_ENTITY_IDS,
    CONF_GRID_NET_POWER_ENTITY_IDS,
    CONF_GRID_NET_POWER_SIGN_CONVENTION,
    CONF_GRID_VOLTAGE_ENTITY_IDS,
    CONF_HEARTBEAT_INTERVAL_SECONDS,
    CONF_HUB_URL,
    CONF_MQTT_PASSWORD,
    CONF_MQTT_USERNAME,
    DEFAULT_GRID_NET_POWER_SIGN_CONVENTION,
    CONF_SITE_ID,
    CONF_TELEMETRY_INTERVAL_SECONDS,
    CONF_TOPIC_PREFIX,
    DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
    DEFAULT_TELEMETRY_INTERVAL_SECONDS,
    DOMAIN,
    ENTITY_SELECTION_CONFIG_KEYS,
    FIXED_HUB_URL,
    GRID_POWER_SIGN_IMPORT_NEGATIVE_EXPORT_POSITIVE,
    GRID_POWER_SIGN_IMPORT_POSITIVE_EXPORT_NEGATIVE,
)
from .hub_client import EnrollmentError, async_enroll_managed_site
from .models import EntrySettings, display_site_title, normalize_entity_ids
from .mqtt_client import async_validate_connection


class EntitySelectionError(Exception):
    """Raised when the entity selection is invalid."""


class CannotConnectError(Exception):
    """Raised when the MQTT broker connection test fails."""


class HATelemetryConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Create, reauth, and reconfigure entries for a single managed site."""

    VERSION = 5

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if self._async_current_entries():
            # Abort before attempting enrollment so a second setup flow cannot
            # consume a token and create another backend site identity.
            return self.async_abort(reason="single_site_supported")

        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                cleaned = await _validate_setup(self.hass, user_input)
            except EntitySelectionError as err:
                errors["base"] = str(err)
            except EnrollmentError as err:
                errors["base"] = err.translation_key
            except CannotConnectError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(cleaned[CONF_SITE_ID])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=display_site_title(cleaned[CONF_SITE_ID]),
                    data=cleaned,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_build_user_schema(user_input or {}),
            errors=errors,
        )

    async def async_step_reauth(self, user_input: dict[str, Any] | None = None):
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                updates = await _validate_reauth(self.hass, entry, user_input)
            except EnrollmentError as err:
                errors["base"] = err.translation_key
            except CannotConnectError:
                errors["base"] = "cannot_connect"
            else:
                self.hass.config_entries.async_update_entry(
                    entry,
                    title=display_site_title(str(updates[CONF_SITE_ID])),
                )
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates=updates,
                    reason="reauth_successful",
                )

        return self.async_show_form(
            step_id="reauth",
            data_schema=_build_reauth_schema(user_input or {}),
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
        entry = self._get_reconfigure_entry()
        defaults = _entry_defaults(entry)
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                updates = _validate_reconfigure(self.hass, user_input)
            except EntitySelectionError as err:
                errors["base"] = str(err)
            else:
                self.hass.config_entries.async_update_entry(
                    entry,
                    title=display_site_title(str(entry.data[CONF_SITE_ID])),
                )
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates=updates,
                    reason="reconfigure_successful",
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_build_reconfigure_schema(defaults),
            errors=errors,
        )


def _entry_defaults(entry: config_entries.ConfigEntry) -> dict[str, Any]:
    merged = dict(entry.data)
    merged.update(entry.options)
    return merged


def _entity_selector(defaults: dict[str, Any], key: str):
    return vol.Optional(
        key,
        default=defaults.get(key, []),
    ), selector.EntitySelector(
        selector.EntitySelectorConfig(
            domain=["sensor"],
            multiple=True,
        )
    )


def _build_shared_entity_fields(defaults: dict[str, Any]) -> dict:
    fields: dict = {}
    for key in (
        CONF_GRID_VOLTAGE_ENTITY_IDS,
        CONF_ADDITIONAL_VOLTAGE_ENTITY_IDS,
        CONF_GRID_FREQUENCY_ENTITY_IDS,
        CONF_ADDITIONAL_FREQUENCY_ENTITY_IDS,
        CONF_GRID_NET_POWER_ENTITY_IDS,
    ):
        schema_key, schema_selector = _entity_selector(defaults, key)
        fields[schema_key] = schema_selector

    fields[vol.Required(
        CONF_GRID_NET_POWER_SIGN_CONVENTION,
        default=defaults.get(
            CONF_GRID_NET_POWER_SIGN_CONVENTION,
            DEFAULT_GRID_NET_POWER_SIGN_CONVENTION,
        ),
    )] = selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                {
                    "value": GRID_POWER_SIGN_IMPORT_POSITIVE_EXPORT_NEGATIVE,
                    "label": "Import positive, export negative",
                },
                {
                    "value": GRID_POWER_SIGN_IMPORT_NEGATIVE_EXPORT_POSITIVE,
                    "label": "Import negative, export positive",
                },
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )

    for key in (
        CONF_GRID_IMPORT_POWER_ENTITY_IDS,
        CONF_GRID_EXPORT_POWER_ENTITY_IDS,
        CONF_ADDITIONAL_POWER_ENTITY_IDS,
    ):
        schema_key, schema_selector = _entity_selector(defaults, key)
        fields[schema_key] = schema_selector

    fields[vol.Required(
        CONF_TELEMETRY_INTERVAL_SECONDS,
        default=defaults.get(CONF_TELEMETRY_INTERVAL_SECONDS, DEFAULT_TELEMETRY_INTERVAL_SECONDS),
    )] = selector.NumberSelector(
        selector.NumberSelectorConfig(min=1, mode=selector.NumberSelectorMode.BOX)
    )
    fields[vol.Required(
        CONF_HEARTBEAT_INTERVAL_SECONDS,
        default=defaults.get(CONF_HEARTBEAT_INTERVAL_SECONDS, DEFAULT_HEARTBEAT_INTERVAL_SECONDS),
    )] = selector.NumberSelector(
        selector.NumberSelectorConfig(min=1, mode=selector.NumberSelectorMode.BOX)
    )
    return fields


def _build_user_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_ENROLLMENT_TOKEN, default=defaults.get(CONF_ENROLLMENT_TOKEN, "")): selector.TextSelector(),
            **_build_shared_entity_fields(defaults),
        }
    )


def _build_reauth_schema(defaults: dict[str, Any]) -> vol.Schema:
    del defaults
    return vol.Schema(
        {
            vol.Required(CONF_ENROLLMENT_TOKEN, default=""): selector.TextSelector(),
        }
    )


def _build_reconfigure_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            **_build_shared_entity_fields(defaults),
        }
    )


def _normalized_entity_selections(user_input: dict[str, Any]) -> dict[str, tuple[str, ...]]:
    return {
        key: normalize_entity_ids(user_input.get(key, []))
        for key in ENTITY_SELECTION_CONFIG_KEYS
    }


def _validate_entity_selection(hass, user_input: dict[str, Any]) -> dict[str, tuple[str, ...]]:
    selections = _normalized_entity_selections(user_input)
    if not any(selections.values()):
        raise EntitySelectionError("sensor_selection_required")

    seen: dict[str, str] = {}
    for key, entity_ids in selections.items():
        for entity_id in entity_ids:
            if entity_id in seen:
                raise EntitySelectionError("duplicate_sensor_selection")
            seen[entity_id] = key

    if selections[CONF_GRID_NET_POWER_ENTITY_IDS] and (
        selections[CONF_GRID_IMPORT_POWER_ENTITY_IDS] or selections[CONF_GRID_EXPORT_POWER_ENTITY_IDS]
    ):
        raise EntitySelectionError("conflicting_grid_power_selection")

    error_key = validate_selected_entities(hass, selections)
    if error_key:
        raise EntitySelectionError(error_key)
    return selections


def _normalize_shared(hass, user_input: dict[str, Any]) -> dict[str, Any]:
    selections = _validate_entity_selection(hass, user_input)
    return {
        **{key: list(entity_ids) for key, entity_ids in selections.items()},
        CONF_GRID_NET_POWER_SIGN_CONVENTION: str(
            user_input.get(
                CONF_GRID_NET_POWER_SIGN_CONVENTION,
                DEFAULT_GRID_NET_POWER_SIGN_CONVENTION,
            )
        ).strip()
        or DEFAULT_GRID_NET_POWER_SIGN_CONVENTION,
        CONF_TELEMETRY_INTERVAL_SECONDS: int(
            user_input.get(CONF_TELEMETRY_INTERVAL_SECONDS, DEFAULT_TELEMETRY_INTERVAL_SECONDS)
        ),
        CONF_HEARTBEAT_INTERVAL_SECONDS: int(
            user_input.get(CONF_HEARTBEAT_INTERVAL_SECONDS, DEFAULT_HEARTBEAT_INTERVAL_SECONDS)
        ),
    }


def _managed_entry_data(local_settings: dict[str, Any], enrollment) -> dict[str, Any]:
    # Local sensor selection stays Home-Assistant-side; the hub owns broker
    # identity and topic namespace.
    return {
        CONF_HUB_URL: FIXED_HUB_URL,
        CONF_HOST: enrollment.mqtt_host,
        CONF_PORT: enrollment.mqtt_port,
        CONF_SITE_ID: enrollment.site_id,
        CONF_TOPIC_PREFIX: enrollment.mqtt_topic_prefix,
        CONF_MQTT_USERNAME: enrollment.mqtt_username,
        CONF_MQTT_PASSWORD: enrollment.mqtt_password,
        **local_settings,
    }


async def _validate_setup(hass, user_input: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_shared(hass, user_input)
    enrollment_token = str(user_input[CONF_ENROLLMENT_TOKEN]).strip()

    enrollment = await async_enroll_managed_site(
        hass,
        hub_url=FIXED_HUB_URL,
        enrollment_token=enrollment_token,
    )

    cleaned = _managed_entry_data(normalized, enrollment)
    settings = EntrySettings.from_mapping(hass, cleaned)
    if not await async_validate_connection(hass, settings):
        raise CannotConnectError
    return cleaned


async def _validate_reauth(hass, entry: config_entries.ConfigEntry, user_input: dict[str, Any]) -> dict[str, Any]:
    enrollment_token = str(user_input[CONF_ENROLLMENT_TOKEN]).strip()
    site_id = str(entry.data[CONF_SITE_ID]).strip()

    enrollment = await async_enroll_managed_site(
        hass,
        hub_url=FIXED_HUB_URL,
        enrollment_token=enrollment_token,
        site_id=site_id,
    )

    local_settings = {
        key: list(entry.data.get(key, []))
        for key in ENTITY_SELECTION_CONFIG_KEYS
    }
    local_settings[CONF_GRID_NET_POWER_SIGN_CONVENTION] = str(
        entry.data.get(
            CONF_GRID_NET_POWER_SIGN_CONVENTION,
            DEFAULT_GRID_NET_POWER_SIGN_CONVENTION,
        )
    ).strip() or DEFAULT_GRID_NET_POWER_SIGN_CONVENTION
    local_settings[CONF_TELEMETRY_INTERVAL_SECONDS] = int(
        entry.data.get(CONF_TELEMETRY_INTERVAL_SECONDS, DEFAULT_TELEMETRY_INTERVAL_SECONDS)
    )
    local_settings[CONF_HEARTBEAT_INTERVAL_SECONDS] = int(
        entry.data.get(CONF_HEARTBEAT_INTERVAL_SECONDS, DEFAULT_HEARTBEAT_INTERVAL_SECONDS)
    )

    updated = _managed_entry_data(local_settings, enrollment)
    settings = EntrySettings.from_mapping(hass, updated)
    if not await async_validate_connection(hass, settings):
        raise CannotConnectError
    return updated


def _validate_reconfigure(hass, user_input: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_shared(hass, user_input)
    normalized[CONF_HUB_URL] = FIXED_HUB_URL
    return normalized
