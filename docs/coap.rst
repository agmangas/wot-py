CoAP
====

This section describes the mapping between the high-level actions that can be executed on a Thing and the
messages exchanged with the server when using the CoAP Protocol Binding.

All messages are serialized in JSON format.

Form elements
-------------

Form elements produced by the CoAP binding vary depending on the type of interaction. All forms contain the following fields:

=============   ===========
Field           Description
=============   ===========
``op``          Interaction verb (e.g. ``readproperty``) associated with this form element.
``href``        The CoAP URL used to interface with the Thing server for this interaction verb.
``mediaType``   This field will always contain the MIME media type for JSON.
=============   ===========

Servers in the CoAP binding expose three distinct resources, one for each interaction type (i.e. property, action and event).
Things and interactions are uniquely identified using query arguments in the CoAP URL for the appropriate resource.

Interaction Model mapping
-------------------------

.. note:: The CoAP binding leverages `CoAP Observe <https://tools.ietf.org/html/rfc7641>`_ to implement server-side messaging when invoking actions or subscribing to properties/events.

Read Property
^^^^^^^^^^^^^

Form::

    {
        "op": "readproperty",
        "contentType": "application/json",
        "href": "coap://<host>:<port>/property?thing=<thing_name>&name=<property_name>"
    }

Request::

    GET coap://<host>:<port>/property?thing=<thing_name>&name=<property_name>

Response::

    CoAP 2.05 Content

    {
        "value": <property_value>
    }

Write Property
^^^^^^^^^^^^^^

Form::

    {
        "op": "writeproperty",
        "contentType": "application/json",
        "href": "coap://<host>:<port>/property?thing=<thing_name>&name=<property_name>"
    }

Request::

    PUT coap://<host>:<port>/property?thing=<thing_name>&name=<property_name>

    {
        "value": <property_value>
    }

Response::

    CoAP 2.04 Changed


Observe Property changes
^^^^^^^^^^^^^^^^^^^^^^^^

Form::

    {
        "op": "observeproperty",
        "contentType": "application/json",
        "href": "coap://<host>:<port>/property?thing=<thing_name>&name=<property_name>"
    }

The interface of the *observe property* verb is equivalent to the *read property* verb with the exception that the client must register as an **observer** (as defined by the RFC) to start receiving server-side messages.

Invoke Action
^^^^^^^^^^^^^

Form::

    {
        "op": "invokeaction",
        "contentType": "application/json",
        "href": "coap://<host>:<port>/action?thing=<thing_name>&name=<action_name>"
    }

An invocation is started by sending a POST request::

    POST coap://<host>:<port>/action?thing=<thing_name>&name=<action_name>

    {
        "input": <action_argument>
    }

The invocation id assigned by the server will be contained in the response::

    CoAP 2.01 Created

    {
        "id": <invocation_id>
    }

The client may check the invocation status by **observing** the resource and passing the invocation id in the payload::

    GET coap://<host>:<port>/action?thing=<thing_name>&name=<action_name>

    {
        "id": <invocation_id>
    }

Invocation status messages sent by the server have the following format::

    CoAP 2.05 Content

    {
        "done": <boolean>,
        "id": <invocation_id>,
        "result" <result_value>,
        "error": <error_message>
    }

Observe Event
^^^^^^^^^^^^^

Form::

    {
        "op": "subscribeevent",
        "contentType": "application/json",
        "href": "coap://<host>:<port>/event?thing=<thing_name>&name=<event_name>"
    }

Subscriptions to the event are created by **observing** the resource::

    GET coap://<host>:<port>/event?thing=<thing_name>&name=<event_name>

Each server response for an active subscription will contain the most recent event emission::

    CoAP 2.05 Content

    {
        "name": <event_name>,
        "data": <event_payload>,
        "time": <timestamp_ms>
    }
