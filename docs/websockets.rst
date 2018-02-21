WebSockets
==========

This section describes the mapping between the high-level actions that can be executed over a Thing and the
messages exchanged with the server when using the WebSockets Protocol Binding.

The format of the messages is based on `JSON-RPC 2.0 <http://www.jsonrpc.org/specification>`_.

Form elements
-------------

Form elements associated with the WebSockets binding that are found in Thing Description documents serialized in
JSON-LD have the following format::

    {
        "href": "ws://agmangas-macpro.fundacionctic.org:9393/TemperatureThing",
        "mediaType": "application/json"
    }

=============   ===========
Field           Description
=============   ===========
``href``        URL where the WebSocket server for this Interaction will respond. The WebSocket server URL is the same for all Interactions in a given Thing.
``mediaType``   This field will always contain the MIME media type for JSON.
=============   ===========

Messages format
---------------

All interactions with the WebSocket server are based on exchanging messages that contain serialized
JSON objects (JSON-RPC).

**Request** messages are sent by the client to interact with one of the Thing Interactions::

    {
        "jsonrpc": "2.0",
        "method": <method_name>,
        "params": <method_params>,
        "id": <message_id>
    }

==========  ========    ===========
Field       Optional    Description
==========  ========    ===========
``method``  No          ID of the method that is being requested (e.g. ``read_property``).
``params``  No          Parameters for the method that is being requested.
``id``      Yes         Message ID of the request. The response message associated with this request will contain the same ID.
==========  ========    ===========

**Response** messages are sent by the server to respond to client requests::

    {
        "jsonrpc": "2.0",
        "result": <request_result>,
        "id": <message_id>
    }

==========  ========    ===========
Field       Optional    Description
==========  ========    ===========
``result``  No          Result for the request that originated this response.
``id``      No          Message ID of the request. If the request didn't contain an ID this field will be *null*.
==========  ========    ===========

**Error** messages are sometimes returned instead of a response if some error arises::

    {
        "jsonrpc": "2.0",
        "error": {
            "code": <error_code>,
            "message": <error_message>,
            "data": <error_data>
        },
        "id": <message_id>
    }

=================   ========    ===========
Field               Optional    Description
=================   ========    ===========
``error.code``      No          Number code that identifies the error.
``error.message``   No          Text description of the error.
``error.data``      Yes         Arbitrary data associated with the error.
``id``              No          Message ID of the request. If the request didn't contain an ID this field will be *null*.
=================   ========    ===========

**Emitted Item** messages are sent for active subscriptions when new events are emitted under that subscription::

    {
        "subscription": <subscription_id>,
        "name": <event_name>,
        "data": <event_payload>
    }

================    ========    ===========
Field               Optional    Description
================    ========    ===========
``subscription``    No          ID of the subscription linked to this emitted item.
``name``            No          Name of the event.
``data``            No          Arbitrary event payload.
================    ========    ===========

Interaction Model mapping
-------------------------

Read Property
^^^^^^^^^^^^^

Request::

    {
        "jsonrpc": "2.0",
        "method": "read_property",
        "params": {"name": "property_name"},
        "id": "09bca9be-7e78-4106-bf4e-e3d503290191"
    }

Response::

    {
        "jsonrpc": "2.0",
        "result": "property_value",
        "id": "09bca9be-7e78-4106-bf4e-e3d503290191"
    }

Write Property
^^^^^^^^^^^^^^

Request::

    {
        "jsonrpc": "2.0",
        "method": "write_property",
        "params": {
            "name": "property_name",
            "value": "property_value"
        },
        "id": "77b06e1f-02dd-4f17-a551-f86045d07099"
    }

Response::

    {
        "jsonrpc": "2.0",
        "result": null,
        "id": "77b06e1f-02dd-4f17-a551-f86045d07099"
    }

Invoke Action
^^^^^^^^^^^^^

Observe Property changes
^^^^^^^^^^^^^^^^^^^^^^^^

Observe Event
^^^^^^^^^^^^^

Observe TD changes
^^^^^^^^^^^^^^^^^^
