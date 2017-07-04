#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wotpy.protocols.server import BaseProtocolServer

import tornado.gen
import tornado.web


# noinspection PyAbstractClass
class ResourceRequestHandler(tornado.web.RequestHandler):
    """Tornado RequestHandler to handle WoT
    interface requests using ResourceListeners."""

    # noinspection PyMethodOverriding
    def initialize(self, resource_listener):
        # noinspection PyAttributeOutsideInit
        self.resource_listener = resource_listener

    @tornado.gen.coroutine
    def get(self):
        future_value = self.resource_listener.on_read()
        value = yield future_value
        self.write({'value': value})

    @tornado.gen.coroutine
    def post(self):
        value = self.get_argument('value')
        yield self.resource_listener.on_write(value)


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
        """Builds a list of handlers for a Tornado application."""

        def _build_url_spec(path, resource_listener):
            return tornado.web.URLSpec(
                path, ResourceRequestHandler,
                kwargs=dict(resource_listener=resource_listener))

        return [
            _build_url_spec(path, resource_listener)
            for path, resource_listener in self._resources.items()]

    def _build_application(self):
        """Builds an instance of a Tornado application to handle the WoT interface requests."""

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
