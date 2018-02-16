#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy

import six

from wotpy.td.jsonld.thing import JsonLDThingDescription


def assert_exposed_thing_equal(exp_thing, td_doc):
    """Asserts that the given ExposedThing is equivalent to the thing description dict."""

    td_expected = copy.deepcopy(td_doc)
    jsonld_td = JsonLDThingDescription(td_expected)

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

    meta_td = jsonld_td.metadata
    meta_exp_thing = exp_thing.thing.semantic_metadata.items

    for key, val in six.iteritems(meta_exp_thing):
        assert key in meta_td
        assert val == meta_td[key]

    # Compare interactions

    for jsonld_interaction in jsonld_td.interaction:
        interaction = exp_thing.thing.find_interaction(jsonld_interaction.name)

        assert sorted(interaction.types) == sorted(jsonld_interaction.type)
        assert getattr(interaction, "output_data", None) == jsonld_interaction.output_data
        assert getattr(interaction, "input_data", None) == jsonld_interaction.input_data
        assert getattr(interaction, "writable", None) == jsonld_interaction.writable
        assert getattr(interaction, "observable", None) == jsonld_interaction.observable
        assert not len(interaction.forms)

        # Compare interaction-level semantic metadata

        meta_td_interaction = jsonld_interaction.metadata
        meta_exp_thing_interaction = interaction.semantic_metadata.items

        for key, val in six.iteritems(meta_exp_thing_interaction):
            assert key in meta_td_interaction
            assert val == meta_td_interaction[key]
