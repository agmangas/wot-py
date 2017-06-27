#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wotpy.protocols.server import BaseProtocolServer


class WebsocketServer(BaseProtocolServer):
    """Websockets server."""

    def __init__(self, port=81, scheme='ws'):
        super(WebsocketServer, self).__init__(port, scheme)

    def add_resource(self, path, resource_listener):
        """"""

        raise NotImplementedError()

    def remove_resource(self, path):
        """"""

        raise NotImplementedError()

    def start(self):
        """Starts the server."""

        raise NotImplementedError()

    def stop(self):
        """Stops the server."""

        raise NotImplementedError()
