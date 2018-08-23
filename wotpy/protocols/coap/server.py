#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class that implements the CoAP server.
"""

import aiocoap
import aiocoap.resource
import six
import tornado.concurrent
import tornado.gen
import tornado.httpserver
import tornado.ioloop
import tornado.web

from wotpy.codecs.enums import MediaTypes
from wotpy.protocols.coap.enums import CoAPSchemes
from wotpy.protocols.coap.resources.property import PropertyReadWriteResource, PropertyObservableResource
from wotpy.protocols.enums import Protocols, InteractionVerbs
from wotpy.protocols.server import BaseProtocolServer
from wotpy.td.enums import InteractionTypes
from wotpy.td.form import Form


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

        return Protocols.COAP

    @property
    def scheme(self):
        """Returns the URL scheme for this server."""

        return CoAPSchemes.COAPS if self.is_secure else CoAPSchemes.COAP

    @property
    def is_secure(self):
        """Returns True if this server is configured to use SSL encryption."""

        return self._ssl_context is not None

    def _build_forms_property(self, proprty, hostname):
        """Builds and returns the CoAP Form instances for the given Property interaction."""

        href_read_write = "{}://{}:{}/{}/property/{}".format(
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
            rel=InteractionVerbs.OBSERVE_PROPERTY)

        return [form_read_write, form_observe]

    def _build_forms_action(self, action, hostname):
        """Builds and returns the CoAP Form instances for the given Action interaction."""

        return []

    def _build_forms_event(self, event, hostname):
        """Builds and returns the CoAP Form instances for the given Event interaction."""

        return []

    def build_forms(self, hostname, interaction):
        """Builds and returns a list with all Form that are
        linked to this server for the given Interaction."""

        intrct_type_map = {
            InteractionTypes.PROPERTY: self._build_forms_property,
            InteractionTypes.ACTION: self._build_forms_action,
            InteractionTypes.EVENT: self._build_forms_event
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

    def _build_root_site(self):
        """Builds and returns the root CoAP Site."""

        root = aiocoap.resource.Site()

        root.add_resource(
            (".well-known", "core"),
            aiocoap.resource.WKCResource(root.get_resources_as_linkheader))

        for exposed_thing in self.exposed_things:
            for name, proprty in six.iteritems(exposed_thing.thing.properties):
                root.add_resource(
                    (exposed_thing.thing.url_name, "property", proprty.url_name),
                    PropertyReadWriteResource(exposed_thing, proprty.name))

                root.add_resource(
                    (exposed_thing.thing.url_name, "property", proprty.url_name, "subscription"),
                    PropertyObservableResource(exposed_thing, proprty.name))

        return root

    def start(self):
        """Starts the CoAP server."""

        if self._future_server is not None:
            return

        self._future_server = tornado.concurrent.Future()

        @tornado.gen.coroutine
        def yield_create_server():
            root = self._build_root_site()
            bind_address = ("::", self.port)
            coap_server = yield aiocoap.Context.create_server_context(root, bind=bind_address)
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
