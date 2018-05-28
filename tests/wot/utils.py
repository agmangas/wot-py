#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy

import six

from wotpy.td.jsonld.description import ThingDescription


def assert_exposed_thing_equal(exp_thing, td_doc):
    """Asserts that the given ExposedThing is equivalent to the thing description dict."""

    td_expected = copy.deepcopy(td_doc)

    for item in td_expected["interaction"]:
        if "link" in item:
            item.pop("link")

    assert exp_thing.name == td_expected.get("name")
    assert exp_thing.thing.types == td_expected.get("@type")

    # Compare semantic context

    ctx_entries = exp_thing.thing.semantic_context.context_entries

    for item in td_expected.get("@context", []):
        if isinstance(item, six.string_types):
            next(ent for ent in ctx_entries if ent.context_url == item and not ent.prefix)
        elif isinstance(item, dict):
            for key, val in six.iteritems(item):
                next(ent for ent in ctx_entries if ent.context_url == val and ent.prefix == key)

    # Compare root-level semantic metadata

    meta_td = ThingDescription.filter_metadata_td(td_expected)
    meta_exp_thing = exp_thing.thing.semantic_metadata.items

    for key, val in six.iteritems(meta_exp_thing):
        assert key in meta_td
        assert val == meta_td[key]

    # Compare interactions

    for item in td_expected.get("interaction", []):
        interaction = exp_thing.thing.find_interaction(item.get("name"))

        assert sorted(interaction.types) == sorted(item.get("@type"))
        assert getattr(interaction, "output_data", None) == item.get("outputData")
        assert getattr(interaction, "input_data", None) == item.get("inputData")
        assert getattr(interaction, "writable", None) == item.get("writable")
        assert getattr(interaction, "observable", None) == item.get("observable")
        assert not len(interaction.forms)

        # Compare interaction-level semantic metadata

        meta_td_interaction = ThingDescription.filter_metadata_interaction(item)
        meta_exp_thing_interaction = interaction.semantic_metadata.items

        for key, val in six.iteritems(meta_exp_thing_interaction):
            assert key in meta_td_interaction
            assert val == meta_td_interaction[key]
