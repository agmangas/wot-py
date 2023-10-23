import asyncio
import re
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

import aiomqtt


@dataclass
class MQTTBrokerURL:
    host: str
    port: int
    username: str = None
    password: str = None

    @classmethod
    def from_url(cls, url):
        regex = re.compile(
            r"^(mqtt[s]?):\/\/(?:(?P<user>[^:@]+)(?::(?P<password>[^@]+))?@)?(?P<host>[^:]+)(?::(?P<port>\d+))?$"
        )

        match = regex.match(url)

        if match:
            host = match.group("host")
            port = int(match.group("port"))
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
            async with client.messages() as messages:
                async for message in messages:
                    await msgs_queue.put(message)
        except asyncio.CancelledError:
            pass
        except Exception as ex:
            await anext_ex_handler(ex)

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
