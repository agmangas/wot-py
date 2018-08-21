#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class that implements the CoAP server.
"""

import aiocoap
import aiocoap.resource as resource
import tornado.concurrent
import tornado.gen
import tornado.httpserver
import tornado.ioloop
import tornado.web

from wotpy.protocols.server import BaseProtocolServer


class CoAPServer(BaseProtocolServer):
    """CoAP binding server implementation."""

    DEFAULT_PORT = 5683

    def __init__(self, port=DEFAULT_PORT, ssl_context=None):
        super(CoAPServer, self).__init__(port=port)
        self._future_server = None
        self._ssl_context = ssl_context

    @property
    def protocol(self):
        """Protocol of this server instance.
        A member of the Protocols enum."""

        raise NotImplementedError

    @property
    def scheme(self):
        """Returns the URL scheme for this server."""

        raise NotImplementedError

    @property
    def is_secure(self):
        """Returns True if this server is configured to use SSL encryption."""

        return self._ssl_context is not None

    def build_forms(self, hostname, interaction):
        """"""

        raise NotImplementedError

    def build_base_url(self, hostname, thing):
        """"""

        raise NotImplementedError

    def _build_root_site(self):
        """Builds and returns the root CoAP Site."""

        root = resource.Site()

        root.add_resource(
            ('.well-known', 'core'),
            resource.WKCResource(root.get_resources_as_linkheader))

        return root

    def start(self):
        """Starts the CoAP server."""

        if self._future_server is not None:
            return

        self._future_server = tornado.concurrent.Future()

        @tornado.gen.coroutine
        def yield_create_server():
            root = self._build_root_site()
            coap_server = yield aiocoap.Context.create_server_context(root)
            self._future_server.set_result(coap_server)

        tornado.ioloop.IOLoop.current().add_callback(yield_create_server)

    def stop(self):
        """Stops the CoAP server."""

        if self._future_server is None:
            return

        def shutdown(ft):
            coap_server = ft.result()

            @tornado.gen.coroutine
            def yield_shutdown():
                yield coap_server.shutdown()

            tornado.ioloop.IOLoop.current().add_callback(yield_shutdown)

        tornado.concurrent.future_add_done_callback(self._future_server, shutdown)

        self._future_server = None
