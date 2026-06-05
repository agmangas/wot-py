#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 CTIC Centro Tecnologico
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
Utility functions used by client and server implementations.
"""

import urllib.parse


def is_scheme_form(form, base, scheme):
    """Returns True if the scheme of the URI for
    the given Form matches the scheme argument."""

    resolved_url = form.resolve_uri(base=base)

    if not resolved_url:
        return False

    parsed_scheme = urllib.parse.urlparse(resolved_url).scheme

    return parsed_scheme in scheme if isinstance(scheme, list) else parsed_scheme == scheme


def pick_form(td, forms, schemes, op=None):
    """Picks the Form that will be used to connect to the remote Thing."""

    for scheme in schemes:
        scheme_forms = [
            form for form in forms
            if is_scheme_form(form, td.base, scheme)
        ]

        if op is not None:
            scheme_forms = [form for form in scheme_forms if form.op == op]

        if len(scheme_forms):
            return scheme_forms[0]

    return None
