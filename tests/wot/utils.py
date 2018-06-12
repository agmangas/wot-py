#!/usr/bin/env python
# -*- coding: utf-8 -*-


def assert_exposed_thing_equal(exp_thing, td_doc):
    """Asserts that the given ExposedThing is equivalent to the Thing Description dict."""

    assert exp_thing.thing.id == td_doc.get("id")
    assert exp_thing.thing.name == td_doc.get("name", None)
    assert exp_thing.thing.description == td_doc.get("description", None)
    assert len(exp_thing.thing.properties) == len(td_doc.get("properties", []))
    assert len(exp_thing.thing.actions) == len(td_doc.get("actions", []))
    assert len(exp_thing.thing.events) == len(td_doc.get("events", []))
