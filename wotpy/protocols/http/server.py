#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class that implements the HTTP server.
"""

import tornado.httpserver
import tornado.web

from wotpy.codecs.enums import MediaTypes
from wotpy.protocols.enums import Protocols
from wotpy.protocols.http.enums import HTTPSchemes
from wotpy.protocols.http.handlers.property import \
    PropertyObserverHandler, \
    PropertyReadWriteHandler
from wotpy.protocols.server import BaseProtocolServer
from wotpy.td.enums import InteractionTypes
from wotpy.td.form import Form


class HTTPServer(BaseProtocolServer):
    """HTTP binding server implementation."""

    DEFAULT_PORT = 80
    REL_OBSERVE = "observeProperty"

    def __init__(self, port=DEFAULT_PORT, ssl_context=None):
        super(HTTPServer, self).__init__(port=port)
        self._server = None
        self._app = self._build_app()
        self._ssl_context = ssl_context

    @property
    def protocol(self):
        """Protocol of this server instance.
        A member of the Protocols enum."""

        return Protocols.HTTP

    @property
    def scheme(self):
        """Returns the URL scheme for this server."""

        return HTTPSchemes.HTTPS if self.is_secure else HTTPSchemes.HTTP

    @property
    def is_secure(self):
        """Returns True if this server is configured to use SSL encryption."""

        return self._ssl_context is not None

    @property
    def app(self):
        """Tornado application."""

        return self._app

    def _build_app(self):
        """Builds and returns the Tornado application for the WebSockets server."""

        return tornado.web.Application([(
            r"/(?P<thing_name>[^\/]+)/(?P<name>[^\/]+)",
            PropertyReadWriteHandler,
            {"http_server": self}
        ), (
            r"/(?P<thing_name>[^\/]+)/(?P<name>[^\/]+)/subscription",
            PropertyObserverHandler,
            {"http_server": self}
        )])

    def _build_forms_property(self, proprty, hostname):
        """Builds and returns the HTTP Form instances for the given Property interaction."""

        href_read_write = "{}://{}:{}/{}/{}".format(
            self.scheme, hostname.rstrip("/").lstrip("/"), self.port,
            proprty.thing.url_name, proprty.url_name)

        form_read_write = Form(
            interaction=proprty,
            protocol=self.protocol,
            href=href_read_write,
            media_type=MediaTypes.JSON)

        href_observe = "{}/subscription".format(href_read_write)

        form_observe = Form(
            interaction=proprty,
            protocol=self.protocol,
            href=href_observe,
            media_type=MediaTypes.JSON,
            rel=self.REL_OBSERVE)

        return [form_read_write, form_observe]

    def build_forms(self, hostname, interaction):
        """Builds and returns a list with all Form that are
        linked to this server for the given Interaction."""

        intrct_type_map = {
            InteractionTypes.PROPERTY: self._build_forms_property
        }

        if interaction.interaction_type not in intrct_type_map:
            raise ValueError("Unsupported interaction")

        return intrct_type_map[interaction.interaction_type](interaction, hostname)

    def build_base_url(self, hostname, thing):
        """Returns the base URL for the given Thing in the context of this server."""

        if not self.exposed_thing_group.find_by_thing_id(thing.id):
            raise ValueError("Unknown Thing")

        return "{}://{}:{}/{}".format(
            self.scheme, hostname.rstrip("/").lstrip("/"),
            self.port, thing.url_name)

    def start(self):
        """Starts the HTTP server."""

        self._server = tornado.httpserver.HTTPServer(self.app, ssl_options=self._ssl_context)
        self._server.listen(self.port)

    def stop(self):
        """Stops the HTTP server."""

        if not self._server:
            return

        self._server.stop()
        self._server = None
