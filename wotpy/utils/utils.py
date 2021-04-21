#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Some utility functions for the WoT data type wrappers.
"""

import json
import socket
from functools import wraps

import six
import tornado.gen


def merge_args_kwargs_dict(args, kwargs):
    """Takes a tuple of args and dict of kwargs.
    Returns a dict that is the result of merging the first item
    of args (if that item is a dict) and the kwargs dict."""

    init_dict = {}

    if len(args) > 0 and isinstance(args[0], dict):
        init_dict = args[0]

    init_dict.update(kwargs)

    return init_dict


def to_camel(val):
    """Takes a string and transforms it to camelCase."""

    if not isinstance(val, six.string_types):
        raise ValueError

    parts = val.split("_")
    parts = parts[:1] + [item.title() for item in parts[1:]]

    return "".join(parts)


def to_snake(val):
    """Takes a string and transforms it to snake_case."""

    if not isinstance(val, six.string_types):
        raise ValueError

    return "".join(["_" + x.lower() if x.isupper() else x for x in val])


def to_json_obj(obj):
    """Recursive function that attempts to convert
    any given object to a JSON-serializable object."""

    if isinstance(obj, set):
        return list(obj)

    try:
        json.dumps(obj)
        return obj
    except TypeError:
        pass

    try:
        return {
            key: to_json_obj(val)
            for key, val in six.iteritems(vars(obj))
        }
    except TypeError:
        raise ValueError("Object {} is not JSON serializable".format(obj))


def get_main_ipv4_address():
    """Returns the main IPv4 address of the current machine in a portable fashion.
    Attribution to the answer provided by Jamieson Becker on:
    https://stackoverflow.com/a/28950776"""

    ip_range = ['10.255.255.255', '10.0.255.255', '10.0.0.255']

    for ip in ip_range:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.connect((ip, 1))
            addr = sock.getsockname()[0]
            sock.close()
            break
        except:
            addr = '127.0.0.1'
        finally:
            sock.close()

    return addr


def handle_observer_finalization(observer):
    """Builds a decorator that yields the wrapped coroutine and calls on_completed
    or on_error on the observer when the coroutine ends or raises an error."""

    def deco(coro):
        @wraps(coro)
        @tornado.gen.coroutine
        def wrapper(*args, **kwargs):
            try:
                yield coro(*args, **kwargs)
                observer.on_completed()
            except Exception as ex:
                observer.on_error(ex)

        return wrapper

    return deco
