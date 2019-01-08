#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
WoT application that consumes the benchmark Thing
and analyzes the captured packet traces.
"""

import argparse
import asyncio
import collections
import copy
import json
import logging
import os
import pprint
import tempfile
import time
import uuid
from subprocess import Popen, PIPE, TimeoutExpired
from urllib.parse import urlparse

import numpy
import pyshark
from tornado.simple_httpclient import HTTPTimeoutError

from wotpy.protocols.enums import Protocols
from wotpy.protocols.http.client import HTTPClient
from wotpy.protocols.ws.client import WebsocketClient
from wotpy.wot.servient import Servient
from wotpy.wot.wot import WoT

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(format=LOG_FORMAT)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.getLogger("wotpy").setLevel(logging.DEBUG)

TARGET_BURST_EVENT = "burstEvent"
TARGET_ROUND_TRIP = "measureRoundTrip"
TARGET_CURR_TIME = "currentTime"

TARGETS = [
    TARGET_BURST_EVENT,
    TARGET_ROUND_TRIP,
    TARGET_CURR_TIME
]


class ConsumedThingCapture(object):
    """Represents a set of packets that have been captured
    from the network interactions with a remote ConsumedThing."""

    START_STOP_WINDOW_SECS = 2.0
    PROCESS_LOOP_SLEEP = 0.1
    PROCESS_TIMEOUT = 0.01

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

        command = [
            "tshark",
            "-i",
            iface,
            "-F",
            "pcapng",
            "-w",
            self._output_file,
            "-f",
            filter_host
        ]

        logger.info("Running capture process: {}".format(command))

        self._process = Popen(command, stdout=PIPE, stderr=PIPE, shell=False)

        await asyncio.sleep(self.START_STOP_WINDOW_SECS)

    async def stop(self):
        """Stops the capture process that is currently in progress."""

        assert self._process
        assert self._output_file

        await asyncio.sleep(self.START_STOP_WINDOW_SECS)

        logger.info("Terminating process: {}".format(self._process))

        self._process.terminate()

        while True:
            try:
                stdout, stderr = self._process.communicate(timeout=self.PROCESS_TIMEOUT)
                break
            except TimeoutExpired:
                pass

            await asyncio.sleep(self.PROCESS_LOOP_SLEEP)

        logger.info("Terminated:\n\tstdout:: {}\n\tstderr:: {}".format(stdout, stderr))

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

        assert protocol in default_ports.keys()

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

        protocol_keys = {
            Protocols.HTTP: "http",
            Protocols.WEBSOCKETS: "websocket",
            Protocols.MQTT: "mqtt"
        }

        protocol_forms = [
            form for form in self._forms_generator()
            if urlparse(form.href).scheme in schemes[protocol]
        ]

        ports = {
            urlparse(form.href).port if urlparse(form.href).port else default_ports[protocol]
            for form in protocol_forms
        }

        display_filter = " or ".join([
            "{}.port == {}".format(transports[protocol], port)
            for port in ports
        ])

        if protocol in protocol_keys:
            display_filter = "({}) and {}".format(display_filter, protocol_keys[protocol])

        return display_filter

    def filter_packets(self, protocol):
        """Returns the set of captured packets that match the given protocol."""

        assert not self._process
        assert self._output_file

        display_filter = self._build_display_filter(protocol)

        logger.info("Building FileCapture for display filter ({}): {}".format(protocol, display_filter))

        return pyshark.FileCapture(self._output_file, display_filter=display_filter)

    def get_capture_size(self, protocol):
        """Returns the total size (bytes) of the captured packets for the given protocol."""

        pyshark_cap = self.filter_packets(protocol)
        size = sum([int(pkt.length) for pkt in pyshark_cap])
        pyshark_cap.close()

        return size


def time_millis():
    """Returns the current timestamp as an integer with ms precision."""

    return int(time.time() * 1000)


def build_protocol_client(protocol):
    """Factory function to build the protocol client for the given protocol."""

    if protocol == Protocols.HTTP:
        return HTTPClient()
    elif protocol == Protocols.WEBSOCKETS:
        return WebsocketClient()
    elif protocol == Protocols.COAP:
        from wotpy.protocols.coap.client import CoAPClient
        return CoAPClient()
    elif protocol == Protocols.MQTT:
        from wotpy.protocols.mqtt.client import MQTTClient
        return MQTTClient()


async def fetch_consumed_thing(td_url, protocol):
    """Gets the remote Thing Description and returns a ConsumedThing."""

    clients = [build_protocol_client(protocol)]
    wot = WoT(servient=Servient(clients=clients))
    consumed_thing = await wot.consume_from_url(td_url)

    return consumed_thing


def count_disordered(arr, size):
    """Counts the number of items that are out of the expected
    order (monotonous increase) in the given list."""

    counter = 0

    state = {
        "expected": next(item for item in range(size) if item in arr),
        "checked": []
    }

    def advance_state():
        state["expected"] += 1

        while True:
            in_arr = state["expected"] in arr
            is_overflow = state["expected"] > size
            not_checked = state["expected"] not in state["checked"]

            if not_checked and (in_arr or is_overflow):
                return

            state["expected"] += 1

    for val in arr:
        if val == state["expected"]:
            advance_state()
        else:
            counter += 1

        state["checked"].append(val)

    return counter


def get_arr_stats(arr):
    """Takes a list of numbers and returns a dict with some statistics."""

    return {
        "mean": numpy.mean(arr).item() if len(arr) else None,
        "median": numpy.median(arr).item() if len(arr) else None,
        "std": numpy.std(arr).item() if len(arr) else None,
        "var": numpy.var(arr).item() if len(arr) else None,
        "max": numpy.max(arr).item() if len(arr) else None,
        "min": numpy.min(arr).item() if len(arr) else None,
        "p95": numpy.percentile(arr, 95).item() if len(arr) else None,
        "p99": numpy.percentile(arr, 99).item() if len(arr) else None
    }


def consume_event_burst(consumed_thing, iface, protocol,
                        sub_sleep=1.0, lambd=5.0, total=10, timeout=10):
    """Gets the stats from invoking the action to initiate
    an event burst and subscribing to those events."""

    stats = {}

    loop = asyncio.get_event_loop()

    cap, events = loop.run_until_complete(_consume_event_burst(
        consumed_thing,
        iface,
        sub_sleep,
        lambd,
        total,
        timeout))

    indexes = [item["index"] for item in events]
    latencies = [item["timeReceived"] - item["timeEmission"] for item in events]

    stats.update({
        "lambd": lambd,
        "total": total,
        "size": cap.get_capture_size(protocol),
        "disordered": count_disordered(indexes, total),
        "loss": 1.0 - (float(len(events)) / total),
        "latency": get_arr_stats(latencies)
    })

    cap.clear()

    return stats


async def _consume_event_burst(consumed_thing, iface, sub_sleep, lambd, total, timeout):
    """Coroutine helper for the consume_event_burst function."""

    burst_id = uuid.uuid4().hex
    done = asyncio.Future()
    events = collections.deque([])

    def on_next(item):
        if item.data.get("id") != burst_id:
            return

        data = copy.deepcopy(item.data)
        data.update({"timeReceived": time_millis()})
        events.append(data)

        logger.info("{}".format(item))

        if item.data.get("burstEnd", False) and not done.done():
            done.set_result(True)

    cap = ConsumedThingCapture(consumed_thing)

    await cap.start(iface)

    logger.info("Subscribing to burst event")

    subscription = consumed_thing.events["burstEvent"].subscribe(
        on_next=on_next,
        on_completed=lambda: logger.info("Completed"),
        on_error=lambda error: logger.warning("Error :: {}".format(error)))

    await asyncio.sleep(sub_sleep)

    logger.info("Invoking action to start event burst")

    await consumed_thing.actions["startEventBurst"].invoke({
        "id": burst_id,
        "lambd": lambd,
        "total": total
    })

    logger.info("Event burst action completed")

    try:
        logger.info("Waiting for last events to arrive")
        await asyncio.wait_for(done, timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning("Timeout waiting for events")

    logger.info("Subscription disposal")

    subscription.dispose()

    await cap.stop()

    return cap, events


def consume_round_trip_action(consumed_thing, iface, protocol, num_batches=10, num_parallel=3):
    """Gets the stats from invoking the action to measure the round trip time."""

    stats = {}

    loop = asyncio.get_event_loop()

    cap, results = loop.run_until_complete(_consume_round_trip_action(
        consumed_thing,
        iface,
        num_batches,
        num_parallel))

    results_ok = [item for item in results if item["success"]]

    latencies_req = [
        item["result"]["timeArrival"] - item["result"]["timeRequest"]
        for item in results_ok
    ]

    latencies_res = [
        item["result"]["timeResponse"] - item["result"]["timeReturn"]
        for item in results_ok
    ]

    latencies = [sum(item) for item in zip(latencies_req, latencies_res)]

    stats.update({
        "numBatches": num_batches,
        "numParallel": num_parallel,
        "size": cap.get_capture_size(protocol),
        "latencyReq": get_arr_stats(latencies_req),
        "latencyRes": get_arr_stats(latencies_res),
        "latency": get_arr_stats(latencies),
        "successRatio": float(len(results_ok)) / len(results)
    })

    cap.clear()

    return stats


async def _consume_round_trip_action(consumed_thing, iface, num_batches, num_parallel):
    """Coroutine helper for the consume_round_trip_action function."""

    results = []

    cap = ConsumedThingCapture(consumed_thing)

    await cap.start(iface)

    action = consumed_thing.actions["measureRoundTrip"]

    for idx in range(num_batches):
        logger.info("Invocation batch {} / {}".format(idx, num_batches))

        invocations = [
            asyncio.ensure_future(action.invoke({"timeRequest": time_millis()}))
            for _ in range(num_parallel)
        ]

        for fut in asyncio.as_completed(invocations):
            item = {}

            try:
                result = await fut
                result.update({"timeResponse": time_millis()})
                item.update({"success": True, "result": result})
            except Exception as ex:
                logger.warning("Error on invocation: {}".format(ex))
                item = {"success": False, "error": ex}

            logger.info("Invocation completed: {}".format("OK" if item["success"] else "ERROR"))

            results.append(item)

    await cap.stop()

    return cap, results


def consume_time_prop(consumed_thing, iface, protocol, rate=20.0, total=100):
    """Gets the stats from consuming the read-only time property."""

    stats = {}

    loop = asyncio.get_event_loop()

    cap, results = loop.run_until_complete(_consume_time_prop(
        consumed_thing,
        iface,
        rate,
        total))

    success_count = len([item for item in results if item["success"]])
    latencies = [item["timeRes"] - item["timeReq"] for item in results]

    stats.update({
        "rate": rate,
        "total": len(results),
        "size": cap.get_capture_size(protocol),
        "successRatio": float(success_count) / len(results),
        "latency": get_arr_stats(latencies)
    })

    cap.clear()

    return stats


async def _consume_time_prop(consumed_thing, iface, rate, total):
    """Coroutine helper for the consume_time_prop function."""

    requests_queue = asyncio.Queue()
    times_req = []
    times_res = []
    req_valid = []
    req_error = []

    async def send_requests():
        """Sends the entire set of requests attempting to honor the given rate."""

        interval_secs = 1.0 / rate
        duration_expected = float(total) / rate

        logger.info("Sending {} total requests".format(total))
        logger.info("Rate: {}/s - Interval: {} s".format(rate, interval_secs))
        logger.info("Total expected duration: {} s".format(duration_expected))

        for idx in range(total):
            req_ini = time.time()
            fut_res = asyncio.ensure_future(consumed_thing.properties["currentTime"].read())
            times_req.append((fut_res, req_ini))
            requests_queue.put_nowait(fut_res)
            sleep_secs = interval_secs - (time.time() - req_ini)
            sleep_secs = sleep_secs if sleep_secs > 0 else 0
            await asyncio.sleep(sleep_secs)

        logger.info("Finished sending requests")

    async def await_response(fut_res):
        """Awaits the given Future response."""

        try:
            await fut_res
            req_valid.append(fut_res)
        except HTTPTimeoutError:
            req_error.append(fut_res)
        except Exception as ex:
            logger.exception(ex)
            req_error.append(fut_res)

        times_res.append((fut_res, time.time()))

    async def consume_requests_queue():
        """Consumes the requests queue to await on every Future response."""

        total_consumed = 0
        awaited_responses = []

        logger.info("Consuming requests queue")

        while total_consumed < total:
            fut_res = await requests_queue.get()
            awaited_res = asyncio.ensure_future(await_response(fut_res))
            awaited_responses.append(awaited_res)
            total_consumed += 1

        logger.info("Finished consuming requests queue")

        await asyncio.wait(awaited_responses)

    cap = ConsumedThingCapture(consumed_thing)

    await cap.start(iface)
    await asyncio.wait([send_requests(), consume_requests_queue()])

    logger.info("Finished processing requests")

    await cap.stop()

    futs_times_req = [item[0] for item in times_req]
    futs_times_res = [item[0] for item in times_res]

    assert set(req_valid + req_error) == set(futs_times_req) == set(futs_times_res)

    results = []

    for res in req_valid + req_error:
        is_success = res in req_valid

        results.append({
            "timeReq": next(int(item[1] * 1000) for item in times_req if item[0] is res),
            "timeRes": next(int(item[1] * 1000) for item in times_res if item[0] is res),
            "result": res.result() if is_success else None,
            "success": is_success
        })

    return cap, results


def parse_args():
    """Parses and returns the command line arguments."""

    parser = argparse.ArgumentParser(description="Benchmark Thing WoT client")

    parser.add_argument(
        "--url",
        dest="td_url",
        required=True,
        help="Benchmark Thing Description URL")

    parser.add_argument(
        "--iface",
        dest="capture_iface",
        required=True,
        help="Network interface to capture packages from")

    parser.add_argument(
        "--protocol",
        dest="protocol",
        required=True,
        choices=Protocols.list(),
        help="Protocol binding that should be used by the WoT client")

    parser.add_argument(
        "--output",
        dest="output",
        required=True,
        help="Path to output JSON file")

    subparsers = parser.add_subparsers(dest="target")
    subparsers.required = True

    parser_burst_event = subparsers.add_parser(TARGET_BURST_EVENT)
    parser_burst_event.set_defaults(target=TARGET_BURST_EVENT)
    parser_burst_event.add_argument("--lambd", dest="lambd", required=True, type=float)
    parser_burst_event.add_argument("--total", dest="total", required=True, type=int)

    parser_round_trip = subparsers.add_parser(TARGET_ROUND_TRIP)
    parser_round_trip.set_defaults(target=TARGET_ROUND_TRIP)
    parser_round_trip.add_argument("--batches", dest="batches", required=True, type=int)
    parser_round_trip.add_argument("--parallel", dest="parallel", required=True, type=int)

    parser_current_time = subparsers.add_parser(TARGET_CURR_TIME)
    parser_current_time.set_defaults(target=TARGET_CURR_TIME)
    parser_current_time.add_argument("--rate", dest="rate", required=True, type=float)
    parser_current_time.add_argument("--total", dest="total", required=True, type=int)

    return parser.parse_args()


def main():
    """Main entrypoint."""

    args = parse_args()

    logger.info("Arguments:\n{}".format(pprint.pformat(vars(args))))

    loop = asyncio.get_event_loop()

    logger.info("Fetching TD from {}".format(args.td_url))

    consumed_thing = loop.run_until_complete(fetch_consumed_thing(
        args.td_url,
        args.protocol))

    logger.info("Consumed Thing: {}".format(consumed_thing))

    def run_target_event_burst():
        logger.info("Consuming burst event (lambd={} total={})".format(args.lambd, args.total))

        ret = consume_event_burst(
            consumed_thing,
            args.capture_iface,
            args.protocol,
            lambd=args.lambd,
            total=args.total)

        logger.info("Stats:\n{}".format(pprint.pformat(ret)))

        return ret

    def run_target_measure_round_trip():
        logger.info("Consuming round trip action (batches={} parallel={})".format(args.batches, args.parallel))

        ret = consume_round_trip_action(
            consumed_thing,
            args.capture_iface,
            args.protocol,
            num_batches=args.batches,
            num_parallel=args.parallel)

        logger.info("Stats:\n{}".format(pprint.pformat(ret)))

        return ret

    def run_current_time():
        logger.info("Consuming time property (rate={} total={})".format(args.rate, args.total))

        ret = consume_time_prop(
            consumed_thing,
            args.capture_iface,
            args.protocol,
            rate=args.rate,
            total=args.total)

        logger.info("Stats:\n{}".format(pprint.pformat(ret)))

        return ret

    func_map = {
        TARGET_CURR_TIME: run_current_time,
        TARGET_ROUND_TRIP: run_target_measure_round_trip,
        TARGET_BURST_EVENT: run_target_event_burst
    }

    stats = func_map[args.target]()
    stats.update({"now": int(time.time() * 1000)})

    logger.info("Serializing results to: {}".format(args.output))

    prev_raw = None

    try:
        with open(args.output, "r") as fh:
            prev_raw = fh.read()
    except FileNotFoundError:
        pass

    with open(args.output, "w") as fh:
        content = json.loads(prev_raw) if prev_raw else {}
        content[args.target] = content[args.target] if content.get(args.target) else {}

        content[args.target][args.protocol] = content[args.target][args.protocol] \
            if content[args.target].get(args.protocol) else []

        content[args.target][args.protocol].append(stats)
        fh.write(json.dumps(content))


if __name__ == "__main__":
    main()
