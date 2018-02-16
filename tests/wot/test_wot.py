#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

# noinspection PyPackageRequirements
from faker import Faker

from tests.td_examples import TD_EXAMPLE
from wotpy.td.semantic import ThingSemanticContextEntry
from wotpy.wot.dictionaries import ThingTemplate, SemanticType, SemanticMetadata
from wotpy.wot.servient import Servient
from wotpy.wot.wot import WoT


def test_produce_td():
    """Things can be produced from thing descriptions serialized to JSON-LD string."""

    td_str = json.dumps(TD_EXAMPLE)
    thing_name = TD_EXAMPLE.get("name")

    servient = Servient()
    wot = WoT(servient=servient)

    exp_thing = wot.produce(td_str)

    assert servient.get_exposed_thing(thing_name)
    assert exp_thing.name == thing_name
    assert len(exp_thing.thing.interactions) == len(TD_EXAMPLE.get("interaction"))


def test_produce_thing_template():
    """Things can be produced from ThingTemplate instances."""

    fake = Faker()

    thing_name = fake.pystr()

    ctx = fake.url()
    ctx_type = fake.pystr()
    ctx_meta_name = fake.pystr()
    ctx_meta_val = fake.pystr()

    sem_type = SemanticType(name=ctx_type, context=ctx)
    sem_meta_type = SemanticType(name=ctx_meta_name, context=ctx)
    sem_meta = SemanticMetadata(semantic_type=sem_meta_type, value=ctx_meta_val)

    thing_template = ThingTemplate(name=thing_name, semantic_types=[sem_type], metadata=[sem_meta])

    servient = Servient()
    wot = WoT(servient=servient)

    exp_thing = wot.produce(thing_template)

    assert servient.get_exposed_thing(thing_name)
    assert exp_thing.name == thing_name
    assert ctx_meta_name in exp_thing.thing.semantic_metadata.items
    assert exp_thing.thing.semantic_metadata.items[ctx_meta_name] == ctx_meta_val
    assert ctx_type in exp_thing.thing.semantic_types.items
    assert ThingSemanticContextEntry(ctx) in exp_thing.thing.semantic_context.context_entries
