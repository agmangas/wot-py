#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Request handler for Property interactions.
"""

import json

from tornado.web import HTTPError

APPLICATION_JSON = "application/json"


def get_exposed_thing(server, thing_name):
    """Utility function to retrieve an ExposedThing
    from the HTTPServer or raise an HTTPError."""

    try:
        return server.get_exposed_thing(thing_name)
    except ValueError:
        raise HTTPError(log_message="Unknown Thing: {}".format(thing_name))


def get_argument(req_handler, name, default=None):
    """Returns an argument extracted from the request.
    Interprets the body as JSON if the Content-Type is application/json.
    Reverts to the default Tornado get_argument otherwise."""

    if req_handler.request.headers.get("Content-Type") != APPLICATION_JSON:
        return req_handler.get_argument(name, default)

    try:
        parsed_body = json.loads(req_handler.request.body)
    except Exception as ex:
        raise HTTPError(log_message="Error decoding JSON: {}".format(ex))

    if not isinstance(parsed_body, dict):
        raise HTTPError(log_message="Not a JSON object: {}".format(parsed_body))

    return parsed_body.get(name, default)
