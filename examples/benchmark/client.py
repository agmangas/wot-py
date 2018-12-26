#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
WoT application that consumes the benchmark Thing
and analyzes the captured packet traces.
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

import pyshark

from wotpy.protocols.enums import Protocols
from wotpy.wot.servient import Servient
from wotpy.wot.wot import WoT

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(format=LOG_FORMAT)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class ConsumedThingCapture(object):
    """Represents a set of packets that have been captured
    from the network interactions with a remote ConsumedThing."""

    START_STOP_WINDOW_SECS = 2.0

    def __init__(self, consumed_thing):
        self._process = None
        self._output_file = None
        self._consumed_thing = consumed_thing

    def _forms_generator(self):
        """Generator that yields every Form in the ConsumedThing."""

        intrct_dicts = [
            self._consumed_thing.properties,
            self._consumed_thing.actions,
            self._consumed_thing.events
        ]

        for intrct_dict in intrct_dicts:
            for name in intrct_dict:
                for form in intrct_dict[name].forms:
                    yield form

    def _get_capture_hosts(self):
        """Returns the list of hosts that are listed in the ConsumedThing Forms."""

        hosts = set()

        for form in self._forms_generator():
            hosts.add(urlparse(form.href).hostname)

        logger.info("Hosts extracted from {}: {}".format(
            self._consumed_thing,
            pprint.pformat(hosts)))

        return list(hosts)

    async def start(self, iface):
        """Starts capturing packets for the ConsumedThing
        hosts in the given network interface."""

        assert not self._process
        assert not self._output_file

        self._output_file = os.path.join(
            tempfile.gettempdir(),
            "{}.pcapng".format(uuid.uuid4().hex))

        filter_host = " or ".join([
            "(host {})".format(item)
            for item in self._get_capture_hosts()
        ])

        command = "tshark -i {} -F pcapng -w {} -f \"{}\"".format(
            iface,
            self._output_file,
            filter_host)

        logger.info("Running capture process: {}".format(command))

        self._process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)

        await asyncio.sleep(self.START_STOP_WINDOW_SECS)

    async def stop(self):
        """Stops the capture process that is currently in progress."""

        assert self._process
        assert self._output_file

        await asyncio.sleep(self.START_STOP_WINDOW_SECS)

        self._process.send_signal(signal.SIGINT)
        stdout, stderr = await self._process.communicate()

        logger.info("Capture terminated:\n\tstdout:: {}\n\tstderr:: {}".format(stdout, stderr))

        self._process = None

    def _remove_output_file(self):
        """Removes the temp pcapng file that contains the captured packets."""

        if not self._output_file:
            return

        logger.info("Removing temp capture file: {}".format(self._output_file))

        os.remove(self._output_file)

    def clear(self):
        """Cleans the internal state to enable this
        instance to capture another set of packets."""

        self._remove_output_file()
        self._process = None
        self._output_file = None

    def _build_display_filter(self, protocol):
        """Returns the Wireshark display filter for packets of the given protocol."""

        default_ports = {
            Protocols.HTTP: 80,
            Protocols.WEBSOCKETS: 81,
            Protocols.MQTT: 1883,
            Protocols.COAP: 5683
        }

        transports = {
            Protocols.HTTP: "tcp",
            Protocols.WEBSOCKETS: "tcp",
            Protocols.MQTT: "tcp",
            Protocols.COAP: "udp"
        }

        schemes = {
            Protocols.HTTP: ["http", "https"],
            Protocols.WEBSOCKETS: ["ws", "wss"],
            Protocols.MQTT: ["mqtt", "mqtts"],
            Protocols.COAP: ["coap", "coaps"]
        }

        protocol_forms = [
            form for form in self._forms_generator()
            if urlparse(form.href).scheme in schemes[protocol]
        ]

        ports = set()

        for form in protocol_forms:
            port = urlparse(form.href).port
            ports.add(port if port else default_ports[protocol])

        display_filter = " or ".join([
            "{}.port == {}".format(transports[protocol], port)
            for port in ports
        ])

        logger.info("Display filter ({}): {}".format(protocol, display_filter))

        return display_filter

    def filter_packets(self, protocol):
        """Returns the set of captured packets that match the given protocol."""

        assert not self._process
        assert self._output_file

        display_filter = self._build_display_filter(protocol)

        return pyshark.FileCapture(self._output_file, display_filter=display_filter)

    def get_capture_size(self, protocol):
        """Returns the total size (bytes) of the captured packets for the given protocol."""

        packets = self.filter_packets(protocol)

        return sum([int(pkt.length) for pkt in packets])


async def consume(td_url):
    """Gets the remote Thing Description and returns a ConsumedThing."""

    wot = WoT(servient=Servient())
    consumed_thing = await wot.consume_from_url(td_url)
    logger.info("ConsumedThing: {}".format(consumed_thing))

    return consumed_thing


async def run_capture(consumed_thing, iface):
    """Consumes the interactions of the remote Thing
    while capturing the exchanged network packets."""

    cap = ConsumedThingCapture(consumed_thing)
    await cap.start(iface)
    action_res = await consumed_thing.actions["measureRoundTrip"].invoke()
    logger.info("Action result: {}".format(action_res))
    await cap.stop()

    return cap


def parse_args():
    """Parses and returns the command line arguments."""

    parser = argparse.ArgumentParser(description="Benchmark Thing WoT client")

    parser.add_argument(
        '--url',
        dest="td_url",
        required=True,
        help="Benchmark Thing Description URL")

    parser.add_argument(
        '--iface',
        dest="capture_iface",
        required=True,
        help="Network interface to capture packages from")

    return parser.parse_args()


def main():
    """Main entrypoint."""

    args = parse_args()
    logger.info("Arguments:\n{}".format(pprint.pformat(vars(args))))
    loop = asyncio.get_event_loop()
    consumed_thing = loop.run_until_complete(consume(args.td_url))
    cap = loop.run_until_complete(run_capture(consumed_thing, args.capture_iface))
    logger.info("Total size: {} bytes".format(cap.get_capture_size(Protocols.WEBSOCKETS)))


if __name__ == "__main__":
    main()
