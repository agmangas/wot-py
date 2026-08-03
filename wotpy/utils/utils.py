#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 CTIC Centro Tecnologico
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
Some utility functions for the WoT data type wrappers.
"""

import json
import socket
import collections.abc
from functools import wraps


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

    if not isinstance(val, str):
        raise ValueError

    parts = val.split("_")
    parts = parts[:1] + [item.title() for item in parts[1:]]

    return "".join(parts)


def to_snake(val):
    """Takes a string and transforms it to snake_case."""

    if not isinstance(val, str):
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
            for key, val in vars(obj).items()
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
        async def wrapper(*args, **kwargs):
            try:
                await coro(*args, **kwargs)
                observer.on_completed()
            except Exception as ex:
                observer.on_error(ex)

        return wrapper

    return deco

def flatten(dictionary, parent_key='', separator='.'):
    """This functions flattens a dictionary converting nested keys
    into simple dot-separated strings.
    Source: https://stackoverflow.com/questions/6027558/flatten-nested-dictionaries-compressing-keys"""

    items = []
    for key, value in dictionary.items():
        new_key = parent_key + separator + key if parent_key else key
        if isinstance(value, collections.abc.MutableMapping):
            items.extend(flatten(value, new_key, separator=separator).items())
        else:
            items.append((new_key, value))
    return dict(items)

def dict_merge(dct, merge_dct):
    """ Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct``.
    :param dct: dict onto which the merge is executed
    :param merge_dct: dct merged into dct
    :return: None
    Source: https://gist.github.com/angstwad/bf22d1822c38a92ec0a9
    """
    for key in merge_dct.keys():
        if (key in dct and isinstance(dct[key], dict) and isinstance(merge_dct[key], dict)):  #noqa
            dict_merge(dct[key], merge_dct[key])
        else:
            dct[key] = merge_dct[key]
