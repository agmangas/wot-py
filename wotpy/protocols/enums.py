#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Enumeration classes related to the various protocol servers.
"""

from wotpy.utils.enums import EnumListMixin


class Protocols(EnumListMixin):
    """Enumeration of protocol types."""

    HTTP = "HTTP"
    WEBSOCKETS = "WEBSOCKETS"


class ProtocolSchemes(EnumListMixin):
    """Enumeration of protocol schemes."""

    HTTP = "http"
    WEBSOCKETS = "ws"

    @classmethod
    def scheme_for_protocol(cls, protocol):
        """Returns the member of this enumeration that is related to the given protocol."""

        protocol_map = {
            Protocols.HTTP: cls.HTTP,
            Protocols.WEBSOCKETS: cls.WEBSOCKETS
        }

        if protocol not in protocol_map:
            raise ValueError("Unknown protocol: {}".format(protocol))

        return protocol_map[protocol]
