#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wotpy.protocols.server import BaseProtocolServer

import tornado.ioloop
import tornado.web


# noinspection PyAbstractClass
class ResourceRequestHandler(tornado.web.RequestHandler):
    """"""

    # noinspection PyMethodOverriding
    def initialize(self, resource_listener):
        # noinspection PyAttributeOutsideInit
        self.resource_listener = resource_listener

    def get(self):
        value = self.resource_listener.on_read()
        self.write({'value': value})


class HttpServer(BaseProtocolServer):
    """HTTP server."""

    def __init__(self, port=80, scheme='http'):
        super(HttpServer, self).__init__(port, scheme)
        self._resources = {}
        self._server = None

    def add_resource(self, path, resource_listener):
        """Adds a resource listener under the given path."""

        self._resources[path] = resource_listener

    def remove_resource(self, path):
        """Removes the resource listener under the given path."""

        self._resources.pop(path)

    def _build_application_handlers(self):
        """"""

        def _build_url_spec(path, resource_listener):
            return tornado.web.URLSpec(
                path, ResourceRequestHandler,
                kwargs=dict(resource_listener=resource_listener))

        return [
            _build_url_spec(path, resource_listener)
            for path, resource_listener in self._resources.items()]

    def _build_application(self):
        """"""

        return tornado.web.Application(self._build_application_handlers())

    def start(self):
        """Starts the server."""

        application = self._build_application()
        self._server = application.listen(self.port)

    def stop(self):
        """Stops the server."""

        if not self._server:
            return

        self._server.stop()
        self._server = None
