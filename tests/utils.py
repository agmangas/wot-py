#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import string

import six
from tornado.escape import to_unicode


def random_alphanum(length=16):
    """Returns a random alphanumeric string."""

    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))


def random_dict_mess(the_dict, num_updates=10, existing_keys_only=False, random_builder=None):
    """Pollutes the given dict adding and updating random keys with random values."""

    def _default_random_builder():
        return [
            random_alphanum(),
            random.random(),
            int(random.random()),
            [random.random() for _ in range(random.randint(1, 10))]
        ]

    random_builder = random_builder if random_builder else _default_random_builder

    for _ in range(num_updates):
        is_new_key = random.choice([True, False]) if not existing_keys_only else False
        the_key = random_alphanum() if is_new_key else random.choice(list(the_dict.keys()))
        the_dict[the_key] = random_builder()


def assert_equal_dict(dict_a, dict_b, compare_as_unicode=False):
    """Asserts that both dicts are equal."""

    assert set(dict_a.keys()) == set(dict_b.keys())

    for key in dict_a:
        value_a = dict_a[key]
        value_b = dict_b[key]

        if compare_as_unicode and isinstance(value_a, six.string_types):
            assert to_unicode(value_a) == to_unicode(value_b)
        else:
            assert value_a == value_b
