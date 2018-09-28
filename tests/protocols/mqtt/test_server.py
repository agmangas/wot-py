#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import uuid
# noinspection PyCompatibility
from asyncio import TimeoutError

import pytest
import six
import tornado.concurrent
import tornado.gen
import tornado.ioloop
from faker import Faker
from hbmqtt.client import MQTTClient
from hbmqtt.mqtt.constants import QOS_2

from tests.protocols.mqtt.broker import is_test_broker_online, BROKER_SKIP_REASON, get_test_broker_url
from wotpy.protocols.enums import InteractionVerbs
from wotpy.protocols.mqtt.handlers.ping import PingMQTTHandler
from wotpy.protocols.mqtt.server import MQTTServer

pytestmark = pytest.mark.skipif(is_test_broker_online() is False, reason=BROKER_SKIP_REASON)


def get_interaction_topic(server, interaction, interaction_verb):
    """Returns the topic for the given interaction and verb."""

    forms = server.build_forms(None, interaction)
    form = next(item for item in forms if interaction_verb in item.rel)
    return "/".join(form.href.split("/")[3:])


@tornado.gen.coroutine
def connect_broker(topics):
    """Connects to the test MQTT broker and subscribes to the topics."""

    topics = [(topics, QOS_2)] if isinstance(topics, six.string_types) else topics

    hbmqtt_client = MQTTClient()
    yield hbmqtt_client.connect(get_test_broker_url())
    yield hbmqtt_client.subscribe(topics)

    raise tornado.gen.Return(hbmqtt_client)


def test_start_stop():
    """The MQTT server may be started and stopped."""

    broker_url = get_test_broker_url()
    mqtt_server = MQTTServer(broker_url=broker_url)

    @tornado.gen.coroutine
    def ping(timeout=None):
        try:
            hbmqtt_client = MQTTClient()
            yield hbmqtt_client.connect(broker_url)
            yield hbmqtt_client.subscribe([(PingMQTTHandler.TOPIC_PONG, QOS_2)])
            bytes_payload = bytes(uuid.uuid4().hex, "utf8")
            yield hbmqtt_client.publish(PingMQTTHandler.TOPIC_PING, bytes_payload, qos=QOS_2)
            message = yield hbmqtt_client.deliver_message(timeout=timeout)
            assert message.data == bytes_payload
            yield hbmqtt_client.disconnect()
        except TimeoutError:
            raise tornado.gen.Return(False)

        raise tornado.gen.Return(True)

    default_timeout = 1.0

    @tornado.gen.coroutine
    def test_coroutine():
        assert not (yield ping(default_timeout))

        yield mqtt_server.start()

        assert (yield ping())
        assert (yield ping())

        yield mqtt_server.stop()
        yield mqtt_server.start()
        yield mqtt_server.stop()

        assert not (yield ping(default_timeout))

        yield mqtt_server.stop()
        yield mqtt_server.start()

        assert (yield ping())

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_property_read(mqtt_server):
    """Current Property values may be requested using the MQTT binding."""

    exposed_thing = next(mqtt_server.exposed_things)
    prop_name = next(six.iterkeys(exposed_thing.thing.properties))
    prop = exposed_thing.thing.properties[prop_name]
    topic_read = get_interaction_topic(mqtt_server, prop, InteractionVerbs.READ_PROPERTY)
    topic_observe = get_interaction_topic(mqtt_server, prop, InteractionVerbs.OBSERVE_PROPERTY)

    observe_timeout_secs = 1.0

    @tornado.gen.coroutine
    def test_coroutine():
        prop_value = Faker().sentence()

        yield exposed_thing.properties[prop_name].write(prop_value)

        client_read = yield connect_broker(topic_read)
        client_observe = yield connect_broker(topic_observe)

        try:
            yield client_observe.deliver_message(timeout=observe_timeout_secs)
            raise AssertionError('Unexpected message on topic {}'.format(topic_observe))
        except TimeoutError:
            pass

        @tornado.gen.coroutine
        def read_value():
            payload = json.dumps({"action": "read"}).encode()
            yield client_read.publish(topic_read, payload, qos=QOS_2)

        periodic_write = tornado.ioloop.PeriodicCallback(read_value, 50)
        periodic_write.start()

        msg_observe = yield client_observe.deliver_message()

        periodic_write.stop()

        assert json.loads(msg_observe.data.decode()).get("value") == prop_value

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_property_write(mqtt_server):
    """Property values may be updated using the MQTT binding."""

    exposed_thing = next(mqtt_server.exposed_things)
    prop_name = next(six.iterkeys(exposed_thing.thing.properties))
    prop = exposed_thing.thing.properties[prop_name]
    topic_write = get_interaction_topic(mqtt_server, prop, InteractionVerbs.WRITE_PROPERTY)
    topic_observe = get_interaction_topic(mqtt_server, prop, InteractionVerbs.OBSERVE_PROPERTY)

    observe_timeout_secs = 1.0

    @tornado.gen.coroutine
    def test_coroutine():
        old_value = Faker().sentence()
        new_value = Faker().sentence()

        yield exposed_thing.properties[prop_name].write(old_value)

        client_write = yield connect_broker(topic_write)
        client_observe = yield connect_broker(topic_observe)

        future_observe = tornado.concurrent.Future()

        @tornado.gen.coroutine
        def resolve_future_on_update():
            msg_observe = yield client_observe.deliver_message()
            assert json.loads(msg_observe.data.decode()).get("value") == new_value
            future_observe.set_result(True)

        tornado.ioloop.IOLoop.current().spawn_callback(resolve_future_on_update)

        @tornado.gen.coroutine
        def write_value():
            payload = json.dumps({"action": "write", "value": new_value}).encode()
            yield client_write.publish(topic_write, payload, qos=QOS_2)

        periodic_write = tornado.ioloop.PeriodicCallback(write_value, 50)
        periodic_write.start()

        yield future_observe

        assert future_observe.result() is True

        periodic_write.stop()

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_observe_property_changes(mqtt_server):
    """Property updates may be observed using the MQTT binding."""

    exposed_thing = next(mqtt_server.exposed_things)
    prop_name = next(six.iterkeys(exposed_thing.thing.properties))
    prop = exposed_thing.thing.properties[prop_name]
    topic_observe = get_interaction_topic(mqtt_server, prop, InteractionVerbs.OBSERVE_PROPERTY)

    @tornado.gen.coroutine
    def test_coroutine():
        yield exposed_thing.properties[prop_name].write(Faker().sentence())

        client_observe = yield connect_broker(topic_observe)

        updated_value = Faker().sentence()

        @tornado.gen.coroutine
        def write_value():
            yield exposed_thing.properties[prop_name].write(updated_value)

        periodic_write = tornado.ioloop.PeriodicCallback(write_value, 50)
        periodic_write.start()

        msg_observe = yield client_observe.deliver_message()

        assert json.loads(msg_observe.data.decode()).get("value") == updated_value

        periodic_write.stop()

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)
