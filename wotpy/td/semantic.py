#!/usr/bin/env python
# -*- coding: utf-8 -*-


class ThingSemanticContext(object):
    """A container for the semantic context entries of a Thing."""

    def __init__(self):
        self._entries = set()

    @property
    def context_entries(self):
        """List of SemanticContextEntry items contained in this instance."""

        return list(self._entries)

    def add(self, context_url, prefix=None):
        """Add a new semantic context entry."""

        entry = ThingSemanticContextEntry(context_url=context_url, prefix=prefix)
        self._entries.add(entry)

    def remove(self, context_url, prefix=None):
        """Remove an existing semantic context entry."""

        entry = ThingSemanticContextEntry(context_url=context_url, prefix=prefix)
        self._entries.discard(entry)

    def to_jsonld_list(self):
        """Returns all context entries as a list, ready to be included
        in the JSON-LD serialization document of the thing."""

        ret = []

        for entry in self._entries:
            if entry.prefix:
                ret.append({entry.prefix: entry.context_url})
            else:
                ret.append(entry.context_url)

        return ret


class ThingSemanticContextEntry(object):
    """An entry in the semantic context of a Thing."""

    def __init__(self, context_url, prefix=None):
        self.context_url = context_url
        self.prefix = prefix

    def __eq__(self, other):
        return self.context_url == other.context_url and \
               self.prefix == other.prefix

    def __hash__(self):
        return hash((self.context_url, self.prefix))


class ThingSemanticMetadata(object):
    """A container for semantic metadata items of Things, Interactions or Forms."""

    def __init__(self):
        self._items = {}

    @property
    def items(self):
        """Dictionary of semantic metadata items."""

        return self._items

    def add(self, key, val):
        """Add a new metadata item."""

        self._items[key] = val

    def remove(self, key):
        """Remove an existing metadata item."""

        self._items.pop(key, None)

    def to_dict(self):
        """Returns the semantic metadata items as a dict."""

        return self._items


class ThingSemanticTypes(object):
    """A container for semantic types of Things or Interactions."""

    def __init__(self):
        self._items = set()

    @property
    def items(self):
        """List of semantic types."""

        return self._items

    def add(self, val):
        """Add a new semantic type."""

        self._items.add(val)

    def remove(self, val):
        """Remove an existing semantic type."""

        self._items.discard(val)

    def to_list(self):
        """Retrns the semantic types as a list."""

        return list(self._items)
