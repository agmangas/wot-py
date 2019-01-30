#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
"""

import logging

from wotpy.protocols.http.server import HTTPServer
from wotpy.protocols.ws.server import WebsocketServer
from wotpy.wot.servient import Servient

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOGGER_NAME = 'wotpy'


def init_logging():
    """Initializes the logging subsystem."""

    logging.basicConfig(format=LOG_FORMAT)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logging.getLogger('wotpy').setLevel(logging.DEBUG)


def build_servient(parsed_args, clients_config=None):
    """Factory function to build a Servient with a set
    of servers depending on the input arguments."""

    logger = logging.getLogger()

    logger.info("Creating servient with TD catalogue on: {}".format(parsed_args.port_catalogue))

    servient = Servient(
        catalogue_port=parsed_args.port_catalogue,
        hostname=parsed_args.hostname,
        clients_config=clients_config)

    if parsed_args.port_ws > 0:
        logger.info("Creating WebSocket server on: {}".format(parsed_args.port_ws))
        servient.add_server(WebsocketServer(port=parsed_args.port_ws))

    if parsed_args.port_http > 0:
        logger.info("Creating HTTP server on: {}".format(parsed_args.port_http))
        servient.add_server(HTTPServer(port=parsed_args.port_http))

    if parsed_args.mqtt_broker:
        try:
            from wotpy.protocols.mqtt.server import MQTTServer
            logger.info("Creating MQTT server on broker: {}".format(parsed_args.mqtt_broker))
            mqtt_server = MQTTServer(parsed_args.mqtt_broker, servient_id=servient.hostname)
            servient.add_server(mqtt_server)
            logger.info("MQTT server created with ID: {}".format(mqtt_server.servient_id))
        except NotImplementedError as ex:
            logger.warning(ex)

    if parsed_args.port_coap > 0:
        try:
            from wotpy.protocols.coap.server import CoAPServer
            logger.info("Creating CoAP server on: {}".format(parsed_args.port_coap))
            servient.add_server(CoAPServer(port=parsed_args.port_coap))
        except NotImplementedError as ex:
            logger.warning(ex)

    return servient


def extend_server_arg_parser(parser):
    """Adds server-related arguments to the given argument parser."""

    parser.add_argument(
        '--port-catalogue',
        dest="port_catalogue",
        default=9090,
        type=int,
        help="Thing Description catalogue port")

    parser.add_argument(
        '--port-http',
        dest="port_http",
        default=9191,
        type=int,
        help="HTTP server port")

    parser.add_argument(
        '--port-ws',
        dest="port_ws",
        default=9292,
        type=int,
        help="WebSockets server port")

    parser.add_argument(
        '--port-coap',
        dest="port_coap",
        default=9393,
        type=int,
        help="CoAP server port")

    parser.add_argument(
        '--mqtt-broker',
        dest="mqtt_broker",
        default="mqtt://localhost",
        help="MQTT broker URL")

    parser.add_argument(
        '--hostname',
        dest="hostname",
        default=None,
        help="Servient hostname")

    return parser
