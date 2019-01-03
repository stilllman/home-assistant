"""
Support for Freebox devices (Freebox v6 and Freebox mini 4K).

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/freebox/
"""
import logging
import socket

import voluptuous as vol

from homeassistant.components.discovery import SERVICE_FREEBOX
from homeassistant.const import CONF_HOST, CONF_PORT, EVENT_HOMEASSISTANT_STOP
from homeassistant.helpers import config_validation as cv, discovery
from homeassistant.helpers.discovery import async_load_platform

REQUIREMENTS = ['aiofreepybox==0.0.6']

_LOGGER = logging.getLogger(__name__)

DOMAIN = "freebox"
DATA_FREEBOX = DOMAIN

FREEBOX_CONFIG_FILE = 'freebox.conf'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PORT): cv.port
    })
}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass, config):
    """Set up the Freebox component."""
    conf = config.get(DOMAIN)

    async def discovery_dispatch(service, discovery_info):
        if conf is None:
            host = discovery_info.get('properties', {}).get('api_domain')
            port = discovery_info.get('properties', {}).get('https_port')
            _LOGGER.info("Discovered Freebox server: %s:%s", host, port)
            await async_setup_freebox(hass, config, host, port)

    discovery.async_listen(hass, SERVICE_FREEBOX, discovery_dispatch)

    if conf is not None:
        host = conf.get(CONF_HOST)
        port = conf.get(CONF_PORT)
        await async_setup_freebox(hass, config, host, port)

    return True


async def async_setup_freebox(hass, config, host, port):
    """Start up the Freebox component platforms."""
    from aiofreepybox import Freepybox
    from aiofreepybox.constants import PERMISSION_SETTINGS
    from aiofreepybox.exceptions import HttpRequestError

    app_desc = {
        'app_id': 'hass',
        'app_name': 'Home Assistant',
        'app_version': '0.65',
        'device_name': socket.gethostname()
        }

    token_file = hass.config.path(FREEBOX_CONFIG_FILE)
    api_version = 'v2'

    fbx = Freepybox(
        app_desc=app_desc,
        token_file=token_file,
        api_version=api_version)

    try:
        await fbx.open(host, port)
    except HttpRequestError:
        _LOGGER.exception('Failed to connect to Freebox')
    else:
        hass.data[DATA_FREEBOX] = fbx

        hass.async_create_task(async_load_platform(
            hass, 'sensor', DOMAIN, {}, config))
        hass.async_create_task(async_load_platform(
            hass, 'device_tracker', DOMAIN, {}, config))
        permissions = await fbx.get_permissions()
        if not permissions.get(PERMISSION_SETTINGS):
            hass.async_create_task(async_load_platform(
                hass, 'switch', DOMAIN, {'perms_settings': False}, config))
            _LOGGER.error('The switch.freebox platform will not be available'
                          ' until you apply the correct permissions in your'
                          ' router. Please refer to documentation : '
                          ' https://home-assistant.io/components/'
                          'switch.freebox/')
        else:
            hass.async_create_task(async_load_platform(
                hass, 'switch', DOMAIN, {'perms_settings': True}, config))

        async def close_fbx(event):
            """Close Freebox connection on HA Stop."""
            await fbx.close()

        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, close_fbx)
