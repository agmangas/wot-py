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
from wotpy.utils.utils import to_json_obj


class ActionMQTTHandler(BaseMQTTHandler):
    """MQTT handler for Action invocations."""

    KEY_INPUT = "input"
    KEY_INVOCATION_ID = "id"

    def __init__(self, mqtt_server, qos=QOS_2):
        super(ActionMQTTHandler, self).__init__(mqtt_server)

        self._qos = qos

    @property
    def topic_wildcard_invocation(self):
        """Wildcard topic to subscribe to all Action invocations."""

        return "{}/action/invocation/#".format(self.servient_id)

    @classmethod
    def to_result_topic(cls, invocation_topic):
        """Takes an Action invocation MQTT topic and returns the related result topic."""

        topic_split = invocation_topic.split("/")
        servient_id, thing_name, action_name = topic_split[-5], topic_split[-2], topic_split[-1]

        return "{}/action/result/{}/{}".format(
            servient_id,
            thing_name,
            action_name)

    def build_action_result_topic(self, thing, action):
        """Returns the MQTT topic for Action invocation results."""

        return "{}/action/result/{}/{}".format(
            self.servient_id,
            thing.url_name,
            action.url_name)

    @property
    def topics(self):
        """List of topics that this MQTT handler wants to subscribe to."""

        return [(self.topic_wildcard_invocation, self._qos)]

    @tornado.gen.coroutine
    def handle_message(self, msg):
        """Listens to all Property request topics and responds to read and write requests."""

        now_ms = int(time.time() * 1000)

        try:
            parsed_msg = json.loads(msg.data.decode())
        except (JSONDecodeError, TypeError):
            return

        topic_split = msg.topic.split("/")

        splits_expected_len = len(self.topic_wildcard_invocation.split("/")) + 1

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

        data = {
            "id": parsed_msg.get(self.KEY_INVOCATION_ID, None),
            "timestamp": now_ms
        }

        try:
            result = yield exp_thing.actions[action.name].invoke(input_value)
            data.update({"result": to_json_obj(result)})
        except Exception as ex:
            data.update({"error": str(ex)})

        topic = self.build_action_result_topic(exp_thing.thing, action)

        yield self.queue.put({
            "topic": topic,
            "data": json.dumps(data).encode(),
            "qos": self._qos
        })
