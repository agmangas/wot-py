#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import json
import logging
import random
import time
import uuid
from contextlib import asynccontextmanager

import aiomqtt
import pytest
from faker import Faker

from tests.protocols.mqtt.broker import (
    BROKER_SKIP_REASON,
    get_test_broker_url,
    is_test_broker_online,
)
from wotpy.protocols.enums import InteractionVerbs
from wotpy.protocols.mqtt.handlers.action import ActionMQTTHandler
from wotpy.protocols.mqtt.server import MQTTServer
from wotpy.protocols.mqtt.utils import MQTTBrokerURL
from wotpy.wot.dictionaries.interaction import ActionFragmentDict, PropertyFragmentDict

pytestmark = pytest.mark.skipif(
    is_test_broker_online() is False, reason=BROKER_SKIP_REASON
)

_logger = logging.getLogger(__name__)


def build_topic(server, interaction, interaction_verb):
    """Returns the topic for the given interaction and verb."""

    forms = server.build_forms(None, interaction)
    form = next(item for item in forms if interaction_verb == item.op)
    return "/".join(form.href.split("/")[3:])


def _client_config():
    mqtt_broker_url = MQTTBrokerURL.from_url(get_test_broker_url())

    return {
        "hostname": mqtt_broker_url.host,
        "port": mqtt_broker_url.port,
        "username": mqtt_broker_url.username,
        "password": mqtt_broker_url.password,
    }


@asynccontextmanager
async def mqtt_client(topics):
    topics = [(topics, 0)] if isinstance(topics, str) else topics

    async with aiomqtt.Client(**_client_config()) as client:
        await asyncio.gather(
            *[client.subscribe(topic=item[0], qos=item[1]) for item in topics]
        )

        yield client


async def _ping(mqtt_server, timeout=None):
    """Returns True if the given MQTT server has answered to a PING request."""

    topic_ping = "{}/ping".format(mqtt_server.servient_id)
    topic_pong = "{}/pong".format(mqtt_server.servient_id)

    bytes_payload = bytes(uuid.uuid4().hex, "utf8")

    try:
        async with aiomqtt.Client(**_client_config()) as client:
            await client.subscribe(topic=topic_pong, qos=2)

            async def read_messages():
                async with client.messages() as messages:
                    async for message in messages:
                        assert message.payload == bytes_payload
                        break

            _logger.debug("Sending PING message: %s", bytes_payload)
            await client.publish(topic_ping, payload=bytes_payload, qos=2)
            await asyncio.wait_for(read_messages(), timeout=timeout)

        return True
    except Exception:
        _logger.warning("Ping error", exc_info=True)
        return False


DEFAULT_PING_TIMEOUT = 2.0


@pytest.mark.asyncio
async def test_start_stop():
    """The MQTT server may be started and stopped."""

    mqtt_server = MQTTServer(broker_url=get_test_broker_url())

    assert not await _ping(mqtt_server, timeout=DEFAULT_PING_TIMEOUT)

    await mqtt_server.start()

    assert await _ping(mqtt_server)
    assert await _ping(mqtt_server)

    await mqtt_server.stop()
    await mqtt_server.start()
    await mqtt_server.stop()

    assert not await _ping(mqtt_server, timeout=DEFAULT_PING_TIMEOUT)

    await mqtt_server.stop()
    await mqtt_server.start()
    await mqtt_server.start()

    assert await _ping(mqtt_server)

    await mqtt_server.stop()


@pytest.mark.asyncio
async def test_servient_id():
    """An MQTT server may be identified by a unique Servient ID to avoid topic collisions."""

    broker_url = get_test_broker_url()

    mqtt_srv_01 = MQTTServer(broker_url=broker_url)
    mqtt_srv_02 = MQTTServer(broker_url=broker_url)
    mqtt_srv_03 = MQTTServer(broker_url=broker_url, servient_id=Faker().pystr())

    assert (
        mqtt_srv_01.servient_id and mqtt_srv_02.servient_id and mqtt_srv_03.servient_id
    )

    assert mqtt_srv_01.servient_id == mqtt_srv_02.servient_id
    assert mqtt_srv_01.servient_id != mqtt_srv_03.servient_id

    async def assert_ping_loop(srv, num_iters=10):
        for _ in range(num_iters):
            assert await _ping(srv, timeout=DEFAULT_PING_TIMEOUT)
            await asyncio.sleep(random.uniform(0.1, 0.3))

    await asyncio.gather(mqtt_srv_01.start(), mqtt_srv_03.start())
    await asyncio.gather(assert_ping_loop(mqtt_srv_01), assert_ping_loop(mqtt_srv_03))
    await asyncio.gather(mqtt_srv_01.stop(), mqtt_srv_03.stop())


@pytest.mark.asyncio
async def test_property_read(mqtt_server):
    """Current Property values may be requested using the MQTT binding."""

    exposed_thing = next(mqtt_server.exposed_things)
    prop_name = next(iter(exposed_thing.thing.properties.keys()))
    prop = exposed_thing.thing.properties[prop_name]
    topic_read = build_topic(mqtt_server, prop, InteractionVerbs.READ_PROPERTY)
    topic_observe = build_topic(mqtt_server, prop, InteractionVerbs.OBSERVE_PROPERTY)
    prop_value = await exposed_thing.properties[prop_name].read()

    async with mqtt_client(topic_read) as client_read:
        async with mqtt_client(topic_observe) as client_observe:
            try:
                async with client_observe.messages() as obs_msgs:
                    logging.debug("Waiting for messages on topic: %s", topic_observe)
                    obs_msg_aiter = obs_msgs.__aiter__()
                    await asyncio.wait_for(obs_msg_aiter.__anext__(), timeout=1.0)
                    raise AssertionError(
                        "Unexpected message on topic {}".format(topic_observe)
                    )
            except asyncio.TimeoutError:
                pass

            stop_event = asyncio.Event()

            async def read_value():
                while not stop_event.is_set():
                    payload = json.dumps({"action": "read"}).encode()
                    await client_read.publish(topic=topic_read, payload=payload, qos=2)
                    await asyncio.sleep(0.05)

            read_task = asyncio.create_task(read_value())

            async with client_observe.messages() as obs_msgs:
                logging.debug("Waiting for messages on topic: %s", topic_observe)
                async for msg in obs_msgs:
                    read_result = msg
                    break

            stop_event.set()
            await read_task

            assert json.loads(read_result.payload.decode()).get("value") == prop_value


@pytest.mark.asyncio
async def test_property_write(mqtt_server):
    """Property values may be updated using the MQTT binding."""

    exposed_thing = next(mqtt_server.exposed_things)
    prop_name = next(iter(exposed_thing.thing.properties.keys()))
    prop = exposed_thing.thing.properties[prop_name]
    topic_write = build_topic(mqtt_server, prop, InteractionVerbs.WRITE_PROPERTY)
    topic_observe = build_topic(mqtt_server, prop, InteractionVerbs.OBSERVE_PROPERTY)
    updated_value = Faker().sentence()

    async with mqtt_client(topic_write) as client_write:
        async with mqtt_client(topic_observe) as client_observe:

            async def wait_for_update():
                async with client_observe.messages() as obs_msgs:
                    async for msg in obs_msgs:
                        assert (
                            json.loads(msg.payload.decode()).get("value")
                            == updated_value
                        )
                        return True

            task_wait_update = asyncio.create_task(wait_for_update())
            stop_event = asyncio.Event()

            async def publish_write():
                while not stop_event.is_set():
                    payload = json.dumps(
                        {"action": "write", "value": updated_value}
                    ).encode()
                    await client_write.publish(
                        topic=topic_write, payload=payload, qos=2
                    )
                    await asyncio.sleep(0.05)

            task_write = asyncio.create_task(publish_write())
            assert await task_wait_update is True
            stop_event.set()
            await task_write


CALLBACK_MS = 50


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mqtt_server", [{"property_callback_ms": CALLBACK_MS}], indirect=True
)
async def test_property_add_remove(mqtt_server):
    """The MQTT binding reacts appropriately to Properties
    being added and removed from ExposedThings."""

    exposed_thing = next(mqtt_server.exposed_things)
    prop_names = list(exposed_thing.thing.properties.keys())

    for name in prop_names:
        exposed_thing.remove_property(name)

    def add_prop(pname):
        exposed_thing.add_property(
            pname,
            PropertyFragmentDict({"type": "number", "observable": True}),
            value=Faker().pyint(),
        )

    def del_prop(pname):
        exposed_thing.remove_property(pname)

    async def is_prop_active(prop, tout=1.0):
        topic_observe = build_topic(
            mqtt_server, prop, InteractionVerbs.OBSERVE_PROPERTY
        )

        topic_write = build_topic(mqtt_server, prop, InteractionVerbs.WRITE_PROPERTY)

        async with mqtt_client(topic_write) as client_write:
            async with mqtt_client(topic_observe) as client_observe:
                value = Faker().pyint()
                stop_event = asyncio.Event()

                async def publish_write():
                    while not stop_event.is_set():
                        payload = json.dumps(
                            {"action": "write", "value": value}
                        ).encode()

                        await client_write.publish(
                            topic=topic_write, payload=payload, qos=0
                        )

                        logging.debug("Published: %s", payload)
                        await asyncio.sleep(tout / 4.0)

                task_write = asyncio.create_task(publish_write())

                try:
                    async with client_observe.messages() as msgs:
                        maiter = msgs.__aiter__()
                        msg = await asyncio.wait_for(maiter.__anext__(), timeout=tout)
                        logging.debug("Received: %s", msg.payload)
                        assert json.loads(msg.payload.decode()).get("value") == value
                        return True
                except asyncio.TimeoutError:
                    logging.debug("Timeout")
                    return False
                finally:
                    stop_event.set()
                    await task_write

    sleep_secs = (CALLBACK_MS / 1000.0) * 4

    prop_01_name = uuid.uuid4().hex
    prop_02_name = uuid.uuid4().hex
    prop_03_name = uuid.uuid4().hex

    add_prop(prop_01_name)
    add_prop(prop_02_name)
    add_prop(prop_03_name)

    prop_01 = exposed_thing.thing.properties[prop_01_name]
    prop_02 = exposed_thing.thing.properties[prop_02_name]
    prop_03 = exposed_thing.thing.properties[prop_03_name]

    await asyncio.sleep(sleep_secs)

    assert await is_prop_active(prop_01)
    assert await is_prop_active(prop_02)
    assert await is_prop_active(prop_03)

    del_prop(prop_01_name)

    assert not (await is_prop_active(prop_01))
    assert await is_prop_active(prop_02)
    assert await is_prop_active(prop_03)

    del_prop(prop_03_name)

    assert not (await is_prop_active(prop_01))
    assert await is_prop_active(prop_02)
    assert not (await is_prop_active(prop_03))

    add_prop(prop_01_name)
    prop_01 = exposed_thing.thing.properties[prop_01_name]

    assert await is_prop_active(prop_01)
    assert await is_prop_active(prop_02)
    assert not (await is_prop_active(prop_03))


@pytest.mark.asyncio
async def test_observe_property_changes(mqtt_server):
    """Property updates may be observed using the MQTT binding."""

    exposed_thing = next(mqtt_server.exposed_things)
    prop_name = next(iter(exposed_thing.thing.properties.keys()))
    prop = exposed_thing.thing.properties[prop_name]
    topic_observe = build_topic(mqtt_server, prop, InteractionVerbs.OBSERVE_PROPERTY)

    async with mqtt_client(topic_observe) as client_observe:
        updated_value = Faker().sentence()
        stop_event = asyncio.Event()

        async def write_value():
            while not stop_event.is_set():
                await exposed_thing.properties[prop_name].write(updated_value)
                await asyncio.sleep(0.05)

        task_write = asyncio.create_task(write_value())

        async with client_observe.messages() as obs_msgs:
            async for msg in obs_msgs:
                observe_result = msg
                break

        assert json.loads(observe_result.payload.decode()).get("value") == updated_value

        stop_event.set()
        await task_write


@pytest.mark.asyncio
async def test_observe_event(mqtt_server):
    """Events may be observed using the MQTT binding."""

    now_ms = int(time.time() * 1000)
    exposed_thing = next(mqtt_server.exposed_things)
    event_name = next(iter(exposed_thing.thing.events.keys()))
    event = exposed_thing.thing.events[event_name]
    topic = build_topic(mqtt_server, event, InteractionVerbs.SUBSCRIBE_EVENT)

    async with mqtt_client(topic) as client:
        emitted_value = Faker().pyint()
        stop_event = asyncio.Event()

        async def emit_value():
            while not stop_event.is_set():
                exposed_thing.events[event_name].emit(emitted_value)
                await asyncio.sleep(0.05)

        task_emit = asyncio.create_task(emit_value())

        async with client.messages() as obs_msgs:
            async for msg in obs_msgs:
                event_result = msg
                break

        event_data = json.loads(event_result.payload.decode())

        assert event_data.get("name") == event_name
        assert event_data.get("data") == emitted_value
        assert event_data.get("timestamp") >= now_ms

        stop_event.set()
        await task_emit


@pytest.mark.asyncio
async def test_action_invoke(mqtt_server):
    """Actions can be invoked using the MQTT binding."""

    exposed_thing = next(mqtt_server.exposed_things)
    action_name = next(iter(exposed_thing.thing.actions.keys()))
    action = exposed_thing.thing.actions[action_name]

    topic_invoke = build_topic(mqtt_server, action, InteractionVerbs.INVOKE_ACTION)
    topic_result = ActionMQTTHandler.to_result_topic(topic_invoke)

    async with mqtt_client(topic_invoke) as client_invoke:
        async with mqtt_client(topic_result) as client_result:
            data = {"id": uuid.uuid4().hex, "input": Faker().pyint()}
            now_ms = int(time.time() * 1000)

            await client_invoke.publish(
                topic=topic_invoke, payload=json.dumps(data).encode(), qos=2
            )

            async with client_result.messages() as msgs:
                async for msg in msgs:
                    msg_data = json.loads(msg.payload.decode())
                    break

            assert msg_data.get("id") == data.get("id")
            assert msg_data.get("result") == "{:f}".format(data.get("input"))
            assert msg_data.get("timestamp") >= now_ms


@pytest.mark.asyncio
async def test_action_invoke_error(mqtt_server):
    """Action errors are handled appropriately by the MQTT binding."""

    exposed_thing = next(mqtt_server.exposed_things)
    action_name = uuid.uuid4().hex
    err_message = Faker().sentence()

    def handler(parameters):
        raise TypeError(err_message)

    exposed_thing.add_action(
        action_name,
        ActionFragmentDict({"input": {"type": "string"}, "output": {"type": "string"}}),
        handler,
    )

    action = exposed_thing.thing.actions[action_name]

    topic_invoke = build_topic(mqtt_server, action, InteractionVerbs.INVOKE_ACTION)
    topic_result = ActionMQTTHandler.to_result_topic(topic_invoke)

    async with mqtt_client(topic_invoke) as client_invoke:
        async with mqtt_client(topic_result) as client_result:
            data = {"id": uuid.uuid4().hex, "input": Faker().pyint()}

            await client_invoke.publish(
                topic=topic_invoke, payload=json.dumps(data).encode(), qos=2
            )

            async with client_result.messages() as msgs:
                async for msg in msgs:
                    msg_data = json.loads(msg.payload.decode())
                    break

            assert msg_data.get("id") == data.get("id")
            assert msg_data.get("error") == err_message
            assert msg_data.get("result", None) is None


@pytest.mark.asyncio
async def test_action_invoke_parallel(mqtt_server):
    """Multiple Actions can be invoked in parallel using the MQTT binding."""

    exposed_thing = next(mqtt_server.exposed_things)
    action_name = next(iter(exposed_thing.thing.actions.keys()))
    action = exposed_thing.thing.actions[action_name]
    topic_invoke = build_topic(mqtt_server, action, InteractionVerbs.INVOKE_ACTION)
    topic_result = ActionMQTTHandler.to_result_topic(topic_invoke)
    num_requests = 10

    async with mqtt_client(topic_invoke) as client_invoke:
        async with mqtt_client(topic_result) as client_result:
            requests = []

            for _ in range(num_requests):
                requests.append({"id": uuid.uuid4().hex, "input": Faker().pyint()})

            now_ms = int(time.time() * 1000)

            await asyncio.gather(
                *[
                    client_invoke.publish(
                        topic=topic_invoke,
                        payload=json.dumps(requests[idx]).encode(),
                        qos=2,
                    )
                    for idx in range(num_requests)
                ]
            )

            for _ in range(num_requests):
                async with client_result.messages() as msgs:
                    async for msg in msgs:
                        msg_data = json.loads(msg.payload.decode())
                        break

                expected = next(
                    item for item in requests if item.get("id") == msg_data.get("id")
                )

                assert msg_data.get("id") == expected.get("id")
                assert msg_data.get("result") == "{:f}".format(expected.get("input"))
                assert msg_data.get("timestamp") >= now_ms
