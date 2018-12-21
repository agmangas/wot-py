#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
"""

import argparse
import asyncio
import logging
import os
import pprint
import signal
import tempfile
import uuid
from urllib.parse import urlparse

from wotpy.wot.servient import Servient
from wotpy.wot.wot import WoT

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(format=LOG_FORMAT)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class CaptureProcess(object):
    """"""

    START_STOP_WINDOW_SECS = 2.0

    def __init__(self):
        self._process = None
        self._output_file = None
        self._output = None

    async def start(self, iface, hosts=None):
        """"""

        assert not self._process
        assert not self._output_file
        assert not self._output

        self._output_file = os.path.join(
            tempfile.gettempdir(),
            "{}.pcapng".format(uuid.uuid4().hex))

        filter_host = None

        if hosts:
            filter_host = " or ".join(["(host {})".format(item) for item in hosts])

        command = "tshark -i {} -F pcapng -w {}".format(
            iface,
            self._output_file)

        if filter_host:
            command = "{} -f \"{}\"".format(command, filter_host)

        logger.info("Running capture process: {}".format(command))

        self._process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)

        await asyncio.sleep(self.START_STOP_WINDOW_SECS)

    async def stop(self):
        """"""

        assert self._process
        assert self._output_file
        assert not self._output

        try:
            await asyncio.sleep(self.START_STOP_WINDOW_SECS)

            self._process.send_signal(signal.SIGINT)
            stdout, stderr = await self._process.communicate()

            logger.info("Capture terminated:\n\tstdout:: {}\n\tstderr:: {}".format(stdout, stderr))

            with open(self._output_file, "rb") as fh:
                self._output = fh.read()

            logger.info("Capture file size: {} KB".format(len(self._output) / 1024.0))
        finally:
            logger.info("Removing temp capture file: {}".format(self._output_file))
            # os.remove(self._output_file)

    def clear(self):
        """"""

        self._process = None
        self._output_file = None
        self._output = None


def get_consumed_thing_hosts(consumed_thing):
    """"""

    hosts = set()

    def add_forms(forms):
        hosts.update({urlparse(item.href).hostname for item in forms})

    intrct_dicts = [
        consumed_thing.properties,
        consumed_thing.actions,
        consumed_thing.events
    ]

    [
        add_forms(intrct_dict[name].forms)
        for intrct_dict in intrct_dicts
        for name in intrct_dict
    ]

    logger.info("Hosts extracted from {}: {}".format(consumed_thing, pprint.pformat(hosts)))

    return list(hosts)


async def main(**kwargs):
    """Subscribes to all events and properties on the remote Thing."""

    td_url = kwargs.pop("td_url")
    capture = kwargs.pop("capture", False)
    iface = kwargs.get("capture_iface")

    assert not capture or iface, "Capture interface required"

    capture_proc = CaptureProcess()

    wot = WoT(servient=Servient())
    consumed_thing = await wot.consume_from_url(td_url)
    consumed_thing_hosts = get_consumed_thing_hosts(consumed_thing)

    logger.info("ConsumedThing: {}".format(consumed_thing))

    if capture:
        await capture_proc.start(iface, hosts=consumed_thing_hosts)

    ret = await consumed_thing.actions["measureRoundTrip"].invoke()

    logger.info("Invocation: {}".format(ret))

    if capture:
        await capture_proc.stop()


def parse_args():
    """Parses and returns the command line arguments."""

    parser = argparse.ArgumentParser(description="Benchmark Thing WoT client")

    parser.add_argument(
        '--url',
        dest="td_url",
        required=True,
        help="Benchmark Thing Description URL")

    parser.add_argument(
        '--capture',
        dest="capture",
        action="store_true",
        help="Capture packages")

    parser.add_argument(
        '--capture-iface',
        dest="capture_iface",
        default=None,
        help="Network interface to capture packages from")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    logger.info("Arguments:\n{}".format(pprint.pformat(vars(args))))
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(**vars(args)))
