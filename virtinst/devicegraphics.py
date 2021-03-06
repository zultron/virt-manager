#
# Copyright 2006-2009, 2013 Red Hat, Inc.
# Jeremy Katz <katzj@redhat.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301 USA.

import os

from virtinst import VirtualDevice
from virtinst.xmlbuilder import XMLProperty


def _get_mode_prop(channel_type):
    xpath = "./channel[@name='%s']/@mode" % channel_type
    return XMLProperty(xpath)


def _validate_port(name, val):
    if val is None:
        return val
    val = int(val)

    if val < 5900 and val != -1:
        raise ValueError(_("%s must be above 5900, or "
                           "-1 for auto allocation") % name)
    return val


class VirtualGraphics(VirtualDevice):
    virtual_device_type = VirtualDevice.VIRTUAL_DEV_GRAPHICS

    TYPE_SDL = "sdl"
    TYPE_VNC = "vnc"
    TYPE_RDP = "rdp"
    TYPE_SPICE = "spice"
    TYPES = [TYPE_VNC, TYPE_SDL, TYPE_RDP, TYPE_SPICE]

    CHANNEL_TYPE_MAIN     = "main"
    CHANNEL_TYPE_DISPLAY  = "display"
    CHANNEL_TYPE_INPUTS   = "inputs"
    CHANNEL_TYPE_CURSOR   = "cursor"
    CHANNEL_TYPE_PLAYBACK = "playback"
    CHANNEL_TYPE_RECORD   = "record"
    CHANNEL_TYPES = [CHANNEL_TYPE_MAIN, CHANNEL_TYPE_DISPLAY,
                     CHANNEL_TYPE_INPUTS, CHANNEL_TYPE_CURSOR,
                     CHANNEL_TYPE_PLAYBACK, CHANNEL_TYPE_RECORD]

    CHANNEL_MODE_SECURE   = "secure"
    CHANNEL_MODE_INSECURE = "insecure"
    CHANNEL_MODE_ANY      = "any"
    CHANNEL_MODES = [CHANNEL_MODE_SECURE, CHANNEL_MODE_INSECURE,
                     CHANNEL_MODE_ANY]

    KEYMAP_LOCAL = "local"
    KEYMAP_DEFAULT = "default"
    _special_keymaps = [KEYMAP_LOCAL, KEYMAP_DEFAULT]

    @staticmethod
    def valid_keymaps():
        """
        Return a list of valid keymap values.
        """
        from virtinst import hostkeymap

        orig_list = hostkeymap.keytable.values()
        sort_list = []

        orig_list.sort()
        for k in orig_list:
            if k not in sort_list:
                sort_list.append(k)

        return sort_list

    @staticmethod
    def pretty_type_simple(gtype):
        if (gtype in [VirtualGraphics.TYPE_VNC,
                      VirtualGraphics.TYPE_SDL,
                      VirtualGraphics.TYPE_RDP]):
            return str(gtype).upper()

        return str(gtype).capitalize()

    def __init__(self, *args, **kwargs):
        VirtualDevice.__init__(self, *args, **kwargs)

        self._local_keymap = -1


    _XML_PROP_ORDER = ["type", "port", "tlsPort", "autoport",
                       "keymap", "listen",
                       "passwd", "display", "xauth"]

    def _default_keymap(self, force_local=False):
        if self.type != "vnc" and self.type != "spice":
            return None

        if (not force_local and
            self.conn.check_support(
                self.conn.SUPPORT_CONN_KEYMAP_AUTODETECT)):
            return None

        if self._local_keymap == -1:
            from virtinst import hostkeymap
            self._local_keymap = hostkeymap.default_keymap()
        return self._local_keymap

    def _set_keymap_converter(self, val):
        if val == self.KEYMAP_DEFAULT:
            return self._default_keymap()
        if val == self.KEYMAP_LOCAL:
            return self._default_keymap(force_local=True)
        return val
    keymap = XMLProperty("./@keymap",
                         default_cb=_default_keymap,
                         set_converter=_set_keymap_converter)

    def _get_default_port(self):
        if self.type == "vnc" or self.type == "spice":
            return -1
        return None
    def _get_default_tlsport(self):
        if self.type == "spice":
            return -1
        return None
    def _get_default_autoport(self):
        # By default, don't do this for VNC to maintain back compat with
        # old libvirt that didn't support 'autoport'
        if self.type != "spice":
            return None
        if (self.port == -1 or self.tlsPort == -1):
            return True
        return None
    port = XMLProperty("./@port", is_int=True,
            set_converter=lambda s, v: _validate_port("Port", v),
            default_cb=_get_default_port)
    tlsPort = XMLProperty("./@tlsPort", is_int=True,
            set_converter=lambda s, v: _validate_port("TLS port", v),
            default_cb=_get_default_tlsport)
    autoport = XMLProperty("./@autoport", is_yesno=True,
                           default_cb=_get_default_autoport)

    channel_main_mode = _get_mode_prop(CHANNEL_TYPE_MAIN)
    channel_display_mode = _get_mode_prop(CHANNEL_TYPE_DISPLAY)
    channel_inputs_mode = _get_mode_prop(CHANNEL_TYPE_INPUTS)
    channel_cursor_mode = _get_mode_prop(CHANNEL_TYPE_CURSOR)
    channel_playback_mode = _get_mode_prop(CHANNEL_TYPE_PLAYBACK)
    channel_record_mode = _get_mode_prop(CHANNEL_TYPE_RECORD)


    def _get_default_display(self):
        if self.type != "sdl":
            return None
        if "DISPLAY" not in os.environ:
            raise RuntimeError("No DISPLAY environment variable set.")
        return os.environ["DISPLAY"]
    def _get_default_xauth(self):
        if self.type != "sdl":
            return None
        return os.path.expanduser("~/.Xauthority")
    xauth = XMLProperty("./@xauth",
                        default_cb=_get_default_xauth)
    display = XMLProperty("./@display",
                          default_cb=_get_default_display)


    type = XMLProperty("./@type",
                       default_cb=lambda s: "vnc",
                       default_name="default")
    listen = XMLProperty("./@listen")
    passwd = XMLProperty("./@passwd")
    passwdValidTo = XMLProperty("./@passwdValidTo")
    socket = XMLProperty("./@socket")


VirtualGraphics.register_type()
