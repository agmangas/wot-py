#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Classes that contain the client logic for the Websocket protocol.
"""

import datetime
import logging
import uuid

import tornado.gen
import tornado.ioloop
import tornado.locks
import tornado.websocket
from rx import Observable
from tornado.concurrent import Future

from wotpy.protocols.client import BaseProtocolClient
from wotpy.protocols.enums import Protocols
from wotpy.protocols.exceptions import FormNotFoundException, ClientRequestTimeout
from wotpy.protocols.refs import ConnRefCounter
from wotpy.protocols.utils import pick_form, is_scheme_form
from wotpy.protocols.ws.enums import WebsocketMethods, WebsocketSchemes
from wotpy.protocols.ws.messages import \
    WebsocketMessageRequest, \
    WebsocketMessageResponse, \
    WebsocketMessageEmittedItem, \
    WebsocketMessageError, \
    WebsocketMessageException
from wotpy.wot.events import \
    PropertyChangeEmittedEvent, \
    EmittedEvent, \
    PropertyChangeEventInit


class WebsocketClient(BaseProtocolClient):
    """Implementation of the protocol client interface for the Websocket protocol."""

    SLEEP_AFTER_ERR_SECS = 1.0
    RECEIVE_LOOP_TERMINATE_SLEEP_SECS = 0.1

    def __init__(self, receive_timeout_secs=1.0, ping_interval=2000):
        self._receive_timeout_secs = receive_timeout_secs
        self._ping_interval = ping_interval
        self._conns = {}
        self._ref_counter = ConnRefCounter()
        self._lock_conn = tornado.locks.Lock()
        self._msg_conditions = {}
        self._messages = {}
        self._receive_stop_events = {}
        self._logr = logging.getLogger(__name__)

    @tornado.gen.coroutine
    def _init_conn(self, ws_url, ref_id):
        """Initializes and connects the WebSockets connection."""

        with (yield self._lock_conn.acquire()):
            self._ref_counter.increase(ws_url, ref_id)

            if ws_url in self._conns:
                return

            self._logr.debug("Connecting to <{}>".format(ws_url))

            self._conns[ws_url] = yield tornado.websocket.websocket_connect(
                ws_url,
                ping_interval=self._ping_interval)

            @tornado.gen.coroutine
            def _start_receive_loop():
                yield self._receive_loop(ws_url)

            self._receive_stop_events[ws_url] = tornado.locks.Event()
            tornado.ioloop.IOLoop.current().add_callback(_start_receive_loop)

    @tornado.gen.coroutine
    def _stop_conn(self, ws_url, ref_id):
        """Disconnects the WebSockets connection."""

        with (yield self._lock_conn.acquire()):
            self._ref_counter.decrease(ws_url, ref_id)

            if self._ref_counter.has_any(ws_url):
                return

            try:
                if ws_url in self._conns:
                    self._logr.debug("Disconnecting WS client: {}".format(ws_url))
                    yield self._conns[ws_url].close()
            except Exception as ex:
                self._logr.warning("Error disconnecting: {}".format(ex), exc_info=True)

            if ws_url in self._receive_stop_events:
                self._logr.debug("Stopping message read loop: {}".format(ws_url))

                self._receive_stop_events[ws_url].set()

                while self._receive_stop_events[ws_url].is_set():
                    yield tornado.gen.sleep(self.RECEIVE_LOOP_TERMINATE_SLEEP_SECS)

                self._receive_stop_events.pop(ws_url)

            self._conns.pop(ws_url, None)
            self._messages.pop(ws_url, None)
            self._msg_conditions.pop(ws_url, None)

    @tornado.gen.coroutine
    def _send_message(self, ws_url, msg_req):
        """Sends a WebSockets message and returns the condition
        that will be notified when the response arrives."""

        if ws_url not in self._conns:
            self._logr.warning("<{}> is not an active connection".format(ws_url))
            return

        if ws_url not in self._msg_conditions:
            self._msg_conditions[ws_url] = {}

        if msg_req.id in self._msg_conditions[ws_url]:
            self._logr.warning("Message condition already exists")

        yield self._conns[ws_url].write_message(msg_req.to_json())

        msg_condition = tornado.locks.Condition()
        self._msg_conditions[ws_url][msg_req.id] = msg_condition

        raise tornado.gen.Return(msg_condition)

    @tornado.gen.coroutine
    def _receive_loop(self, ws_url):
        """Starts the WebSockets message receiving loop."""

        if ws_url not in self._conns:
            self._logr.warning("<{}> is not an active connection".format(ws_url))
            return

        if ws_url not in self._messages:
            self._messages[ws_url] = {}

        while not self._receive_stop_events[ws_url].is_set():
            try:
                raw_res = yield self._conns[ws_url].read_message()

                self._logr.debug("Read message: {}".format(raw_res))

                if raw_res is None:
                    self._logr.debug("Cannot read message: Closed WS connection")
                    yield tornado.gen.sleep(self.SLEEP_AFTER_ERR_SECS)
                    continue

                msg_res = self._parse_msg_response(raw_res)

                if msg_res:
                    self._messages[ws_url][msg_res.id] = msg_res
                    conditions = self._msg_conditions.get(ws_url, None)

                    if conditions and msg_res.id in conditions:
                        self._logr.debug("Notifying: {}".format(msg_res.id))
                        conditions[msg_res.id].notify_all()
            except Exception as ex:
                self._logr.warning("Error in read loop: {}".format(ex), exc_info=True)
                yield tornado.gen.sleep(self.SLEEP_AFTER_ERR_SECS)

        self._receive_stop_events[ws_url].clear()

    @classmethod
    def _parse_msg_response(cls, raw_msg):
        """Returns a parsed WS Response message instance if
        the raw message format is valid and has the given ID.
        Raises Exception if the WS message is an error."""

        try:
            return WebsocketMessageResponse.from_raw(raw_msg)
        except WebsocketMessageException:
            pass

        try:
            return WebsocketMessageError.from_raw(raw_msg)
        except WebsocketMessageException:
            pass

        return None

    @classmethod
    def _parse_emitted_item(cls, raw_msg, sub_id):
        """Returns a parsed WS Emitted Item message instance if
        the raw message format is valid and has the given ID.
        Raises Exception if the WS message is an error."""

        try:
            msg = WebsocketMessageEmittedItem.from_raw(raw_msg)

            if msg.subscription_id == sub_id:
                return msg
        except WebsocketMessageException:
            pass

        try:
            err = WebsocketMessageError.from_raw(raw_msg)
            err_sub_id = err.data and err.data.get("subscription")

            if err_sub_id == sub_id:
                raise Exception(err.message)
        except WebsocketMessageException:
            pass

        return None

    @property
    def protocol(self):
        """Protocol of this client instance.
        A member of the Protocols enum."""

        return Protocols.WEBSOCKETS

    def _build_subscribe(self, ws_url, msg_req, on_next):
        """Builds the subscribe function that is passed
        as an argument on the creation of an Observable."""

        def subscribe(observer):
            """Connect to the WS server and start passing the received events to the Observer."""

            future_sub_id = Future()
            future_ws_conn = Future()

            def on_error(ex):
                observer.on_error(ex)

            def on_next_event(raw_msg):
                sub_id = future_sub_id.result()

                try:
                    msg_item = self._parse_emitted_item(raw_msg, sub_id)
                except Exception as ex:
                    return on_error(ex)

                if msg_item is None:
                    return

                try:
                    on_next(observer, msg_item)
                except Exception as ex:
                    return on_error(ex)

            def parse_subscription_id(raw_msg):
                msg_res = self._parse_msg_response(raw_msg)

                if isinstance(msg_res, WebsocketMessageError):
                    return on_error(Exception(msg_res.message))

                if msg_res is None:
                    return

                sub_id = msg_res.result
                future_sub_id.set_result(sub_id)

            def on_msg(raw_msg):
                if raw_msg is None:
                    return on_error(Exception("WS connection closed"))

                if future_sub_id.done():
                    on_next_event(raw_msg)
                else:
                    parse_subscription_id(raw_msg)

            def on_conn(ft):
                try:
                    ws_conn = ft.result()
                except Exception as ex:
                    return on_error(ex)

                future_ws_conn.set_result(ws_conn)
                ws_conn.write_message(msg_req.to_json())

            tornado.websocket.websocket_connect(ws_url, callback=on_conn, on_message_callback=on_msg)

            def unsubscribe():
                if future_ws_conn.done():
                    ws_conn = future_ws_conn.result()
                    ws_conn.close()

            return unsubscribe

        return subscribe

    def is_supported_interaction(self, td, name):
        """Returns True if the any of the Forms for the Interaction
        with the given name is supported in this Protocol Binding client."""

        forms = td.get_forms(name)

        forms_wss = [
            form for form in forms
            if is_scheme_form(form, td.base, WebsocketSchemes.WSS)
        ]

        forms_ws = [
            form for form in forms
            if is_scheme_form(form, td.base, WebsocketSchemes.WS)
        ]

        return len(forms_wss) or len(forms_ws)

    def _raise_message(self, ws_url, msg_id):
        """Raises the error or return Exception from the message
        in the internal collection matching the given ID."""

        assert ws_url in self._messages, "Unknown WS connection"
        assert msg_id in self._messages[ws_url], "Unknown message ID"

        msg = self._messages[ws_url][msg_id]

        if isinstance(msg, WebsocketMessageError):
            raise Exception(msg.message)
        else:
            raise tornado.gen.Return(msg.result)

    @tornado.gen.coroutine
    def invoke_action(self, td, name, input_value, timeout=None):
        """Invokes an Action on a remote Thing.
        Returns a Future."""

        if name not in td.actions:
            raise FormNotFoundException()

        form = pick_form(
            td, td.get_action_forms(name),
            WebsocketSchemes.list())

        if not form:
            raise FormNotFoundException()

        ws_url = form.resolve_uri(td.base)
        ref_id = uuid.uuid4().hex

        try:
            yield self._init_conn(ws_url, ref_id)

            msg_req = WebsocketMessageRequest(
                method=WebsocketMethods.INVOKE_ACTION,
                params={"name": name, "parameters": input_value},
                msg_id=uuid.uuid4().hex)

            condition = yield self._send_message(ws_url, msg_req)

            timeout = datetime.timedelta(seconds=timeout) if timeout else None
            cond_res = yield condition.wait(timeout=timeout)

            if not cond_res:
                raise ClientRequestTimeout

            self._raise_message(ws_url, msg_req.id)
        finally:
            yield self._stop_conn(ws_url, ref_id)

    @tornado.gen.coroutine
    def write_property(self, td, name, value, timeout=None):
        """Updates the value of a Property on a remote Thing.
        Returns a Future."""

        if name not in td.properties:
            raise FormNotFoundException()

        form = pick_form(
            td, td.get_property_forms(name),
            WebsocketSchemes.list())

        if not form:
            raise FormNotFoundException()

        ws_url = form.resolve_uri(td.base)
        ref_id = uuid.uuid4().hex

        try:
            yield self._init_conn(ws_url, ref_id)

            msg_req = WebsocketMessageRequest(
                method=WebsocketMethods.WRITE_PROPERTY,
                params={"name": name, "value": value},
                msg_id=uuid.uuid4().hex)

            condition = yield self._send_message(ws_url, msg_req)

            timeout = datetime.timedelta(seconds=timeout) if timeout else None
            cond_res = yield condition.wait(timeout=timeout)

            if not cond_res:
                raise ClientRequestTimeout

            self._raise_message(ws_url, msg_req.id)
        finally:
            yield self._stop_conn(ws_url, ref_id)

    @tornado.gen.coroutine
    def read_property(self, td, name, timeout=None):
        """Reads the value of a Property on a remote Thing.
        Returns a Future."""

        if name not in td.properties:
            raise FormNotFoundException()

        form = pick_form(
            td, td.get_property_forms(name),
            WebsocketSchemes.list())

        if not form:
            raise FormNotFoundException()

        ws_url = form.resolve_uri(td.base)
        ref_id = uuid.uuid4().hex

        try:
            yield self._init_conn(ws_url, ref_id)

            msg_req = WebsocketMessageRequest(
                method=WebsocketMethods.READ_PROPERTY,
                params={"name": name},
                msg_id=uuid.uuid4().hex)

            condition = yield self._send_message(ws_url, msg_req)

            timeout = datetime.timedelta(seconds=timeout) if timeout else None
            cond_res = yield condition.wait(timeout=timeout)

            if not cond_res:
                raise ClientRequestTimeout

            self._raise_message(ws_url, msg_req.id)
        finally:
            yield self._stop_conn(ws_url, ref_id)

    def on_event(self, td, name):
        """Subscribes to an event on a remote Thing.
        Returns an Observable."""

        if name not in td.events:
            # noinspection PyUnresolvedReferences
            return Observable.throw(FormNotFoundException())

        form = pick_form(
            td, td.get_event_forms(name),
            WebsocketSchemes.list())

        if not form:
            # noinspection PyUnresolvedReferences
            return Observable.throw(FormNotFoundException())

        ws_url = form.resolve_uri(td.base)

        msg_req = WebsocketMessageRequest(
            method=WebsocketMethods.ON_EVENT,
            params={"name": name},
            msg_id=uuid.uuid4().hex)

        def on_next(observer, msg_item):
            observer.on_next(EmittedEvent(init=msg_item.data, name=name))

        subscribe = self._build_subscribe(ws_url, msg_req, on_next)

        # noinspection PyUnresolvedReferences
        return Observable.create(subscribe)

    def on_property_change(self, td, name):
        """Subscribes to property changes on a remote Thing.
        Returns an Observable."""

        if name not in td.properties:
            # noinspection PyUnresolvedReferences
            return Observable.throw(FormNotFoundException())

        form = pick_form(
            td, td.get_property_forms(name),
            WebsocketSchemes.list())

        if not form:
            # noinspection PyUnresolvedReferences
            return Observable.throw(FormNotFoundException())

        ws_url = form.resolve_uri(td.base)

        msg_req = WebsocketMessageRequest(
            method=WebsocketMethods.ON_PROPERTY_CHANGE,
            params={"name": name},
            msg_id=uuid.uuid4().hex)

        def on_next(observer, msg_item):
            init_name = msg_item.data["name"]
            init_value = msg_item.data["value"]
            init = PropertyChangeEventInit(name=init_name, value=init_value)
            observer.on_next(PropertyChangeEmittedEvent(init=init))

        subscribe = self._build_subscribe(ws_url, msg_req, on_next)

        # noinspection PyUnresolvedReferences
        return Observable.create(subscribe)

    def on_td_change(self, url):
        """Subscribes to Thing Description changes on a remote Thing.
        Returns an Observable."""

        raise NotImplementedError
