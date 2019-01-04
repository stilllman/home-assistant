"""
Support for Freebox devices (Freebox v6 and Freebox mini 4K).

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/switch.freebox/
"""
import logging

from homeassistant.components.freebox import DATA_FREEBOX
from homeassistant.const import (STATE_OFF, STATE_ON)
from homeassistant.helpers.entity import ToggleEntity

DEPENDENCIES = ['freebox']

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
        hass, config, add_entities, discovery_info=None):
    """Set up the sensors."""
    fbx = hass.data[DATA_FREEBOX]
    perms_settings = discovery_info.get('perms_settings')
    add_entities([
        FbxWifiSwitch(fbx, perms_settings),
    ])


class FbxWifiSwitch(ToggleEntity):
    """Representation of a freebox wifi switch."""

    def __init__(self, fbx, perms_settings):
        """Initilize the Wifi switch."""
        self._name = 'Freebox WiFi'
        self._state = STATE_OFF
        self.perms_settings = perms_settings
        self.fbx = fbx

    @property
    def available(self):
        """If permission is not true the switch is not available."""
        if not self.perms_settings:
            return False
        return True

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def state(self):
        """Return the state of the switch."""
        return self._state

    @property
    def should_poll(self):
        """Poll for status."""
        return True

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state == STATE_ON

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        wifi_config = {"enabled": True}
        await self.fbx.wifi.set_global_config(wifi_config)

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        wifi_config = {"enabled": False}
        await self.fbx.wifi.set_global_config(wifi_config)

    async def async_update(self):
        """Get the state and update it."""
        from aiofreepybox.constants import PERMISSION_SETTINGS

        permissions = await self.fbx.get_permissions()
        if permissions.get(PERMISSION_SETTINGS):
            self.perms_settings = True
        else:
            self.perms_settings = False

        datas = await self.fbx.wifi.get_global_config()
        active = datas['enabled']
        self._state = STATE_ON if active else STATE_OFF
