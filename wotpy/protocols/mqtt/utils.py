# Copyright (c) 2023 CTIC Centro Tecnologico
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

import asyncio
import re
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

import aiomqtt

_DEFAULT_MQTT_PORT = 1883


@dataclass
class MQTTBrokerURL:
    host: str
    port: int
    username: str = None
    password: str = None

    @classmethod
    def from_url(cls, url):
        regex = re.compile(
            r"^(mqtt[s]?):\/\/(?:(?P<user>[^:@]+)(?::(?P<password>[^@]+))?@)?(?P<host>[^:]+)(?::(?P<port>\d+))?\/?$"
        )

        match = regex.match(url)

        if match:
            host = match.group("host")

            try:
                port = int(match.group("port"))
            except TypeError:
                port = _DEFAULT_MQTT_PORT

            username = match.group("user")
            password = match.group("password")

            return cls(host=host, port=port, username=username, password=password)
        else:
            raise ValueError("Invalid URL")


async def aiomqtt_read_loop(
    stop_event: asyncio.Event,
    client: aiomqtt.Client,
    anext_ex_handler: Callable[[Exception], Awaitable[Any]],
    message_handler: Callable[[aiomqtt.Message], Awaitable[Any]],
):
    msgs_queue = asyncio.Queue()

    async def produce_messages():
        try:
            while not stop_event.is_set():
                try:
                    async with client.messages() as messages:
                        async for message in messages:
                            await msgs_queue.put(message)
                except Exception as ex:
                    await anext_ex_handler(ex)
        except asyncio.CancelledError:
            pass

    async def consume_messages():
        try:
            while True:
                message = await msgs_queue.get()
                await message_handler(message)
        except asyncio.CancelledError:
            pass

    task_produce = asyncio.create_task(produce_messages())
    task_consume = asyncio.create_task(consume_messages())

    await stop_event.wait()

    task_consume.cancel()
    task_produce.cancel()

    await asyncio.gather(task_produce, task_consume)
