#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2025 National Technical University of Athens
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# SPDX-License-Identifier: MIT

"""
Zenoh handler for Action invocations.
"""

import json
import time
from json import JSONDecodeError

from wotpy.protocols.zenoh.handlers.base import BaseZenohHandler
from wotpy.utils.utils import to_json_obj


class ActionZenohHandler(BaseZenohHandler):
    """Zenoh handler for Action invocations."""

    KEY_INPUT = "input"
    KEY_INVOCATION_ID = "id"

    def __init__(self, zenoh_server):
        super().__init__(zenoh_server)

    @property
    def topic_wildcard_invocation(self):
        """Wildcard topic to subscribe to all Action invocations."""

        return "{}/action/invocation/**".format(self.servient_id)

    @classmethod
    def to_result_topic(cls, invocation_topic):
        """Takes an Action invocation Zenoh topic and returns the related result topic."""

        topic_split = invocation_topic.split("/")
        servient_id, thing_name, action_name = topic_split[-5], topic_split[-2], topic_split[-1]

        return "{}/action/result/{}/{}".format(
            servient_id,
            thing_name,
            action_name)

    def build_action_result_topic(self, thing, action):
        """Returns the Zenoh topic for Action invocation results."""

        return "{}/action/result/{}/{}".format(
            self.servient_id,
            thing.url_name,
            action.url_name)

    @property
    def topics(self):
        """List of topics that this Zenoh handler wants to subscribe to."""

        return [(self.topic_wildcard_invocation)]

    async def handle_message(self, sample):
        """Listens to all Property request topics and responds to read and write requests."""

        now_ms = int(time.time() * 1000)

        try:
            parsed_msg = json.loads(sample.payload.to_string())
        except (JSONDecodeError, TypeError):
            return

        topic_split = str(sample.key_expr).split("/")

        splits_expected_len = len(self.topic_wildcard_invocation.split("/")) + 1

        if len(topic_split) != splits_expected_len:
            return

        thing_url_name, action_url_name = topic_split[-2], topic_split[-1]

        try:
            exp_thing = next(
                item for item in self.zenoh_server.exposed_things
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
            result = await exp_thing.actions[action.name].invoke(input_value)
            data.update({"result": to_json_obj(result)})
        except Exception as ex:
            data.update({"error": str(ex)})

        topic = self.build_action_result_topic(exp_thing.thing, action)

        await self.queue.put({
            "topic": topic,
            "data": json.dumps(data).encode()
        })
