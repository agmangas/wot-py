#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Zenoh utility functions.
"""

import json

import zenoh


def build_zenoh_config(router_url):
    """Builds a Zenoh config that connects to a Zenoh router in client mode."""

    config = zenoh.Config()

    config.insert_json5("mode", json.dumps("client"))
    router_url = router_url if router_url.startswith("tcp/") else f"tcp/{router_url}"
    config.insert_json5("connect/endpoints", json.dumps([router_url]))

    return config
