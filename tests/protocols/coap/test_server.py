#!/usr/bin/env python
# -*- coding: utf-8 -*-

import aiocoap
import tornado.gen
import tornado.ioloop

from wotpy.protocols.coap.server import CoAPServer


def test_start_stop():
    """The CoAP server can be started and stopped."""

    coap_server = CoAPServer()
    ping_uri = "coap://127.0.0.1/.well-known/core"

    @tornado.gen.coroutine
    def ping():
        try:
            coap_client = yield aiocoap.Context.create_client_context()
            request = aiocoap.Message(code=aiocoap.Code.GET, uri=ping_uri)
            response = yield coap_client.request(request).response
        except Exception:
            raise tornado.gen.Return(False)

        raise tornado.gen.Return(response.code.is_successful())

    @tornado.gen.coroutine
    def test_coroutine():
        assert not (yield ping())

        coap_server.start()
        yield tornado.gen.sleep(0)

        assert (yield ping())
        assert (yield ping())

        coap_server.stop()
        yield tornado.gen.sleep(0)

        assert not (yield ping())

        coap_server.stop()
        coap_server.start()
        coap_server.start()
        yield tornado.gen.sleep(0)

        assert (yield ping())

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)
