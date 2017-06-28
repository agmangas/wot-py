#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import string


def random_alphanum(length=8):
    """Returns a random alphanumeric string."""

    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))


def random_dict_mess(the_dict, num_updates=8, existing_keys_only=False):
    """Pollutes the given dict adding and updating random keys with random values."""

    def build_random_value():
        return [
            random_alphanum(),
            random.random(),
            int(random.random()),
            [random.random() for _ in range(random.randint(1, 10))]
        ]

    for _ in range(num_updates):
        is_new_key = random.choice([True, False]) if not existing_keys_only else False
        the_key = random_alphanum() if is_new_key else random.choice(list(the_dict.keys()))
        the_dict[the_key] = build_random_value()
