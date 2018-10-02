#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MQTT handler for Action invocations.
"""

import json
import time
from json import JSONDecodeError

import tornado.gen
import tornado.ioloop
from hbmqtt.mqtt.constants import QOS_2

from wotpy.protocols.mqtt.handlers.base import BaseMQTTHandler
from wotpy.utils.serialization import to_json_obj


class ActionMQTTHandler(BaseMQTTHandler):
    """MQTT handler for Action invocations."""

    KEY_INPUT = "input"
    KEY_INVOCATION_ID = "id"
    TOPIC_ACTION_INVOCATION_WILDCARD = "action/invocation/#"

    def __init__(self, mqtt_server, qos=QOS_2):
        super(ActionMQTTHandler, self).__init__(mqtt_server)

        self._qos = qos

    @classmethod
    def to_result_topic(cls, invocation_topic):
        """Takes an Action invocation MQTT topic and returns the related result topic."""

        splitted_topic = invocation_topic.split("/")
        splitted_topic[1] = "result"
        return "/".join(splitted_topic)

    @classmethod
    def build_action_invocation_topic(cls, thing, action):
        """Returns the MQTT topic for Action invocations."""

        topic = "action/invocation/{}/{}".format(thing.url_name, action.url_name)
        assert cls.TOPIC_ACTION_INVOCATION_WILDCARD.replace("#", "") in topic
        return topic

    @classmethod
    def build_action_result_topic(cls, thing, action):
        """Returns the MQTT topic for Action invocation results."""

        return "action/result/{}/{}".format(thing.url_name, action.url_name)

    @property
    def topics(self):
        """List of topics that this MQTT handler wants to subscribe to."""

        return [(self.TOPIC_ACTION_INVOCATION_WILDCARD, self._qos)]

    @tornado.gen.coroutine
    def handle_message(self, msg):
        """Listens to all Property request topics and responds to read and write requests."""

        now_ms = int(time.time() * 1000)

        try:
            parsed_msg = json.loads(msg.data.decode())
        except (JSONDecodeError, TypeError):
            return

        topic_split = msg.topic.split("/")

        splits_expected_len = len(self.TOPIC_ACTION_INVOCATION_WILDCARD.split("/")) + 1

        if len(topic_split) != splits_expected_len:
            return

        thing_url_name, action_url_name = topic_split[-2], topic_split[-1]

        try:
            exp_thing = next(
                item for item in self.mqtt_server.exposed_things
                if item.url_name == thing_url_name)

            action = next(
                exp_thing.thing.actions[key] for key in exp_thing.thing.actions
                if exp_thing.thing.actions[key].url_name == action_url_name)
        except StopIteration:
            return

        input_value = parsed_msg.get(self.KEY_INPUT, None)
        result = yield exp_thing.actions[action.name].invoke(input_value)
        topic = self.build_action_result_topic(exp_thing.thing, action)

        data = {
            "id": parsed_msg.get(self.KEY_INVOCATION_ID, None),
            "result": to_json_obj(result),
            "timestamp": now_ms
        }

        yield self.queue.put({
            "topic": topic,
            "data": json.dumps(data).encode(),
            "qos": self._qos
        })
