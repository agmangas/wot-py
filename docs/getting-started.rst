.. Copyright (c) 2026 Contributors to the Eclipse Foundation

.. _getting-started:

Getting Started with wotpy
==========================

wotpy is a Python implementation of the `W3C WoT Runtime and Scripting API <https://www.w3.org/WoT/>`__.
It lets you build Things (producers) and Consumers in Python, with built-in protocol bindings for HTTP, WebSockets, MQTT, CoAP, and Zenoh.

This guide gets you up and running using the **Smart Coffee Machine** example.
By the end you will have a Thing and a Consumer running locally and talking to each other.

Installation
------------

Install wotpy from PyPI:

.. code-block:: bash

    pip install wotpy

For development — running the examples from the repository — you need a virtual environment with the project installed in editable mode.

* Using ``pip``:

  .. code-block:: bash

      python3 -m venv .venv
      .venv/bin/pip install -U -e ".[tests]"
      .venv/bin/pip install -r examples/coffee-machine/requirements.txt

* Using ``uv``:

  .. code-block:: bash

      uv venv .venv
      uv sync --extra tests
      .venv/bin/pip install -r examples/coffee-machine/requirements.txt

If you have `Taskfile <https://taskfile.dev/installation/>`__ **v3.28 or later** installed, the first two steps can be replaced with ``task venv`` (pip) or ``task uv-venv`` (uv).

Running the example
-------------------

Open two terminals in the repository root.

**Terminal 1 — start the Thing (server)**

.. code-block:: bash

    .venv/bin/python examples/coffee-machine/server.py

You should see output similar to::

    INFO     coffee-machine:server.py Creating WebSocket server on: 9393
    INFO     coffee-machine:server.py Creating HTTP server on: 9494
    INFO     coffee-machine:server.py Creating servient with TD catalogue on: 9090
    INFO     coffee-machine:server.py Starting servient
    INFO     coffee-machine:server.py Exposing and configuring Thing
    INFO     coffee-machine:server.py Smart-Coffee-Machine is ready

The server exposes three endpoints:

* ``http://localhost:9090`` — Thing Description catalogue (lists all available Things)
* ``http://localhost:9494`` — HTTP protocol binding
* ``ws://localhost:9393`` — WebSocket protocol binding

**Terminal 2 — run the Consumer (client)**

The client discovers the Thing's URL automatically from the catalogue, so no manual configuration is needed:

.. code-block:: bash

    .venv/bin/python examples/coffee-machine/client.py

What the coffee machine exposes
--------------------------------

The Thing Description defines the following interactions:

Properties
^^^^^^^^^^

=============================  =========  ============================================================
Property                       Type       Description
=============================  =========  ============================================================
``allAvailableResources``      object     Current percentage of water, milk, chocolate, and coffeeBeans
``possibleDrinks``             array      Fixed list of available drink types
``servedCounter``              integer    Total number of drinks served so far
``maintenanceNeeded``          boolean    Set to ``True`` automatically when ``servedCounter`` > 1000; observable
``schedules``                  array      List of scheduled drink tasks
=============================  =========  ============================================================

Actions
^^^^^^^

``makeDrink``
    Brew a drink. Accepts ``drinkId``, ``size`` (``s``/``m``/``l``), and ``quantity`` (1–5).
    Defaults to one medium americano if no input is provided.
    Returns ``{"result": true, "message": "..."}`` on success.

``setSchedule``
    Add a recurring or one-off brew schedule. ``time`` (24 h format) and ``mode`` (e.g. ``everyday``, ``everyMo``) are required.

Events
^^^^^^

``outOfResource``
    Emitted when a requested drink cannot be made because a resource (water, milk, etc.) has run out.

Reading the client output
--------------------------

When the client runs successfully you will see log lines showing each interaction in sequence:

1. Read ``allAvailableResources`` (all at 100 %)
2. Write water level down to 80 % and read it back
3. Subscribe to ``maintenanceNeeded`` observable property
4. Invoke ``makeDrink`` for 3 large lattes and log the result
5. Read ``allAvailableResources`` again to see resource consumption
6. Invoke ``setSchedule`` for a daily espresso at 10:00
7. Read ``schedules`` to confirm it was stored
8. Subscribe to the ``outOfResource`` event
9. Wait 60 seconds for any incoming events, then exit

Next steps
----------

* :ref:`protocols` — learn how properties, actions, and events map to raw HTTP, WebSocket, MQTT, CoAP, and Zenoh messages
* :ref:`authentication` — add security to your Things
* :ref:`genindex` — full API reference
