HTTP
====

This section describes the mapping between the high-level actions that can be executed on a Thing and the
messages exchanged with the server when using the HTTP Protocol Binding.

All messages are serialized in JSON format.

Form elements
-------------

Form elements produced by the HTTP binding vary depending on the type of interaction. All forms contain the following fields:

=============   ===========
Field           Description
=============   ===========
``op``          Interaction verb (e.g. ``readproperty``) associated with this form element.
``href``        The HTTP URL used to interface with the Thing server for this interaction verb.
``mediaType``   This field will always contain the MIME media type for JSON.
=============   ===========

Interaction Model mapping
-------------------------

.. note:: The HTTP binding adopts the *long-polling* pattern to deal with server-side messages. In practice, this means that the server will keep the connection open on requests to the *action invocation*, *property subscription* and *event subscription* endpoints until a value is emitted or a timeout occurs.

Read Property
^^^^^^^^^^^^^

Form::

    {
        "op": "readproperty",
        "contentType": "application/json",
        "href": "http://<host>:<port>/<thing_name>/property/<property_name>"
    }

Request::

    GET http://<host>:<port>/<thing_name>/property/<property_name>

Response::

    HTTP 200

    {
        "value": <property_value>
    }

Write Property
^^^^^^^^^^^^^^

Form::

    {
        "op": "writeproperty",
        "contentType": "application/json",
        "href": "http://<host>:<port>/<thing_name>/property/<property_name>"
    }

Request::

    PUT http://<host>:<port>/<thing_name>/property/<property_name>

    {
        "value": <property_value>
    }

Response::

    HTTP 200

Invoke Action
^^^^^^^^^^^^^

Form::

    {
        "op": "invokeaction",
        "contentType": "application/json",
        "href": "http://<host>:<port>/<thing_name>/action/<action_name>"
    }

An action invocation can be started with a POST request::

    POST http://<host>:<port>/<thing_name>/action/<action_name>

    {
        "input": <action_argument>
    }

A unique UUID will be assigned to the ongoing invocation and returned in the response::

    HTTP 200

    {
        "invocation": "/invocation/<uuid>"
    }

The status of the invocation can be retrieved from that URL::

    GET http://<host>:<port>/invocation/<uuid>

The response will contain the final ``result`` or an ``error`` message::

    HTTP 200

    {
        "done": <boolean>,
        "result" <result_value>,
        "error": <error_message>
    }


Observe Property changes
^^^^^^^^^^^^^^^^^^^^^^^^

Form::

    {
        "op": "observeproperty",
        "contentType": "application/json",
        "href": "http://<host>:<port>/<thing_name>/property/<property_name>/subscription"
    }

Subscriptions are automatically managed by the HTTP binding. A subscription is initialized on each request and cancelled after a value is emitted::

    GET http://<host>:<port>/<thing_name>/property/<property_name>/subscription

The response format is the same as the *read property* verb::

    HTTP 200

    {
        "value": <property_value>
    }

Observe Event
^^^^^^^^^^^^^

Form::

    {
        "op": "subscribeevent",
        "contentType": "application/json",
        "href": "http://<host>:<port>/<thing_name>/event/<event_name>/subscription"
    }

Request::

    GET http://<host>:<port>/<thing_name>/event/<event_name>/subscription

Response::

    HTTP 200

    {
        "payload": <event_payload>
    }

Please note that subscriptions are also managed automatically, as occurs in the *observe property* case.