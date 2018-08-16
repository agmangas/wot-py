#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility functions used by client and server implementations.
"""

from six.moves import urllib


def is_scheme_form(form, base, scheme):
    """Returns True if the scheme of the URI for
    the given Form matches the scheme argument."""

    resolved_url = form.resolve_uri(base=base)

    if not resolved_url:
        return False

    return urllib.parse.urlparse(resolved_url).scheme == scheme


def pick_form_for_schemes(td, forms, schemes):
    """Picks the Form that will be used to connect to the remote Thing."""

    for scheme in schemes:
        scheme_forms = [
            form for form in forms
            if is_scheme_form(form, td.base, scheme)
        ]

        if len(scheme_forms):
            return scheme_forms[0]

    return None
