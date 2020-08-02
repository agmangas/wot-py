#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
WoT application to expose a Thing that provides simulated temperature values.
"""
import json
import logging
import random
import math
import six

import tornado.gen
from tornado.concurrent import Future
from tornado.ioloop import IOLoop, PeriodicCallback

from wotpy.protocols.http.server import HTTPServer
from wotpy.protocols.ws.server import WebsocketServer
from wotpy.wot.servient import Servient

CATALOGUE_PORT = 9090
WEBSOCKET_PORT = 9393
HTTP_PORT = 9494

logging.basicConfig()
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

TD = {
    "title": 'Smart-Coffee-Machine',
    "id": 'urn:dev:wot:example:coffee-machine',
    "description": '''A smart coffee machine with a range of capabilities.
A complementary tutorial is available at http://www.thingweb.io/smart-coffee-machine.html.''',
    "support": 'git://github.com/eclipse/thingweb.node-wot.git',
    '@context': [
        'https://www.w3.org/2019/wot/td/v1',
    ],
    "properties": {
        "allAvailableResources": {
            "type": 'object',
            "description": '''Current level of all available resources given as an integer percentage for each particular resource.
The data is obtained from the machine's sensors but can be set manually in case the sensors are broken.''',
            "properties": {
                "water": {
                    "type": 'integer',
                    "minimum": 0,
                    "maximum": 100,
                },
                "milk": {
                    "type": 'integer',
                    "minimum": 0,
                    "maximum": 100,
                },
                "chocolate": {
                    "type": 'integer',
                    "minimum": 0,
                    "maximum": 100,
                },
                "coffeeBeans": {
                    "type": 'integer',
                    "minimum": 0,
                    "maximum": 100,
                },
            },
        },
        "possibleDrinks": {
            "type": 'array',
            "description": '''The list of possible drinks in general. Doesn't depend on the available resources.''',
            "items": {
                "type": 'string',
            }
        },
        "servedCounter": {
            "type": 'integer',
            "description": '''The total number of served beverages.''',
            "minimum": 0,
        },
        "maintenanceNeeded": {
            "type": 'boolean',
            "description": '''Shows whether a maintenance is needed. The property is observable. Automatically set to True when the servedCounter property exceeds 1000.''',
            "observable": True,
        },
        "schedules": {
            "type": 'array',
            "description": '''The list of scheduled tasks.''',
            "items": {
                "type": 'object',
                "properties": {
                    "drinkId": {
                        "type": 'string',
                        "description": '''Defines what drink to make, drinkId is one of possibleDrinks property values, e.g. latte.''',
                    },
                    "size": {
                        "type": 'string',
                        "description": '''Defines the size of a drink, s = small, m = medium, l = large.''',
                        "enum": ['s', 'm', 'l'],
                    },
                    "quantity": {
                        "type": 'integer',
                        "description": '''Defines how many drinks to make, ranging from 1 to 5.''',
                        "minimum": 1,
                        "maximum": 5,
                    },
                    "time": {
                        "type": 'string',
                        "description": '''Defines the time of the scheduled task in 24h format, e.g. 10:00 or 21:00.''',
                    },
                    "mode": {
                        "type": 'string',
                        "description": '''Defines the mode of the scheduled task, e.g. once or everyday. All the possible values are given in the enum field of this Thing Description.''',
                        "enum": ['once', 'everyday', 'everyMo', 'everyTu', 'everyWe', 'everyTh', 'everyFr', 'everySat', 'everySun'],
                    },
                },
            },
        },
    },
    "actions": {
        "makeDrink": {
            "description": '''Make a drink from available list of beverages. Accepts drink id, size and quantity as input.
Brews one medium americano if no input is specified.''',
            "input": {
                "type": 'object',
                "properties": {
                    "drinkId": {
                        "type": 'string',
                        "description": '''Defines what drink to make, drinkId is one of possibleDrinks property values, e.g. latte.''',
                    },
                    "size": {
                        "type": 'string',
                        "description": '''Defines the size of a drink, s = small, m = medium, l = large.''',
                        "enum": ['s', 'm', 'l'],
                    },
                    "quantity": {
                        "type": 'integer',
                        "description": '''Defines how many drinks to make, ranging from 1 to 5.''',
                        "minimum": 1,
                        "maximum": 5
                    },
                },
            },
            "output": {
                "type": 'object',
                "description": '''Returns True/false and a message when all invoked promises are resolved (asynchronous).''',
                "properties": {
                    "result": {
                        "type": 'boolean',
                    },
                    "message": {
                        "type": 'string',
                    },
                },
            },
        },
        "setSchedule": {
            "description": '''Add a scheduled task to the schedules property. Accepts drink id, size, quantity, time and mode as body of a request.
Assumes one medium americano if not specified, but time and mode are mandatory fields.''',
            "input": {
                "type": 'object',
                "properties": {
                    "drinkId": {
                        "type": 'string',
                        "description": '''Defines what drink to make, drinkId is one of possibleDrinks property values, e.g. latte.''',
                    },
                    "size": {
                        "type": 'string',
                        "description": '''Defines the size of a drink, s = small, m = medium, l = large.''',
                        "enum": ['s', 'm', 'l'],
                    },
                    "quantity": {
                        "type": 'integer',
                        "description": '''Defines how many drinks to make, ranging from 1 to 5.''',
                        "minimum": 1,
                        "maximum": 5
                    },
                    "time": {
                        "type": 'string',
                        "description": '''Defines the time of the scheduled task in 24h format, e.g. 10:00 or 21:00.''',
                    },
                    "mode": {
                        "type": 'string',
                        "description": '''Defines the mode of the scheduled task, e.g. once or everyday. All the possible values are given in the enum field of this Thing Description.''',
                        "enum": ['once', 'everyday', 'everyMo', 'everyTu', 'everyWe', 'everyTh', 'everyFr', 'everySat', 'everySun'],
                    },
                },
                "required": ['time', 'mode'],
            },
            "output": {
                "type": 'object',
                "description": '''Returns True/false and a message when all invoked promises are resolved (asynchronous).''',
                "properties": {
                    "result": {
                        "type": 'boolean',
                    },
                    "message": {
                        "type": 'string',
                    },
                },
            },
        },
    },
    "events": {
        "outOfResource": {
            "description": '''Out of resource event. Emitted when the available resource level is not sufficient for a desired drink.''',
            "data": {
                "type": 'string',
            },
        },
    },
}


@tornado.gen.coroutine
def main():
    LOGGER.info("Creating WebSocket server on: {}".format(WEBSOCKET_PORT))
    ws_server = WebsocketServer(port=WEBSOCKET_PORT)

    LOGGER.info("Creating HTTP server on: {}".format(HTTP_PORT))
    http_server = HTTPServer(port=HTTP_PORT)

    LOGGER.info("Creating servient with TD catalogue on: {}".format(CATALOGUE_PORT))
    servient = Servient(catalogue_port=CATALOGUE_PORT)
    servient.add_server(ws_server)
    servient.add_server(http_server)

    LOGGER.info("Starting servient")
    wot = yield servient.start()

    LOGGER.info("Exposing and configuring Thing")

    # Produce the Thing from Thing Description
    exposed_thing = wot.produce(json.dumps(TD))

    # Initialize the property values
    yield exposed_thing.properties['allAvailableResources'].write({
        'water': read_from_sensor('water'),
        'milk': read_from_sensor('milk'),
        'chocolate': read_from_sensor('chocolate'),
        'coffeeBeans': read_from_sensor('coffeeBeans'),
    })
    yield exposed_thing.properties['possibleDrinks'].write(['espresso', 'americano', 'cappuccino', 'latte', 'hotChocolate', 'hotWater'])
    yield exposed_thing.properties['maintenanceNeeded'].write(False)
    yield exposed_thing.properties['schedules'].write([])
    
    # # Observe the value of maintenanceNeeded property
    exposed_thing.properties['maintenanceNeeded'].subscribe(

        # Notify a "maintainer" when the value has changed
        # (the notify function here simply logs a message to the console)

        on_next=lambda data: notify(f'Value changed for an observable property: {data}'),
        on_completed=notify('Subscribed for an observable property: maintenanceNeeded'),
        on_error=lambda error: notify(f'Error for an observable property maintenanceNeeded: {error}')
    )
    
    # Override a write handler for servedCounter property,
    # raising maintenanceNeeded flag when the value exceeds 1000 drinks
    @tornado.gen.coroutine
    def served_counter_write_handler(value):

        yield exposed_thing._default_update_property_handler('servedCounter', value)

        if value > 1000:
            yield exposed_thing.properties['maintenanceNeeded'].write(True)

    exposed_thing.set_property_write_handler('servedCounter', served_counter_write_handler)

    # Now initialize the servedCounter property
    yield exposed_thing.properties['servedCounter'].write(read_from_sensor('servedCounter'))

    # Set up a handler for makeDrink action
    async def make_drink_action_handler(params):
        params = params['input'] if params['input'] else {}
        
        # Default values
        drinkId = 'americano'
        size = 'm'
        quantity = 1
        
        # Size quantifiers
        sizeQuantifiers = {'s': 0.1, 'm': 0.2, 'l': 0.3}
        
        # Drink recipes showing the amount of a resource consumed for a particular drink
        drinkRecipes = {
            'espresso': {
                'water': 1,
                'milk': 0,
                'chocolate': 0,
                'coffeeBeans': 2,
            },
            'americano': {
                'water': 2,
                'milk': 0,
                'chocolate': 0,
                'coffeeBeans': 2,
            },
            'cappuccino': {
                'water': 1,
                'milk': 1,
                'chocolate': 0,
                'coffeeBeans': 2,
            },
            'latte': {
                'water': 1,
                'milk': 2,
                'chocolate': 0,
                'coffeeBeans': 2,
            },
            'hotChocolate': {
                'water': 0,
                'milk': 0,
                'chocolate': 1,
                'coffeeBeans': 0,
            },
            'hotWater': {
                'water': 1,
                'milk': 0,
                'chocolate': 0,
                'coffeeBeans': 0,
            },
        }

        # Check if params are provided
        drinkId = params.get('drinkId', drinkId)
        size = params.get('size', size)
        quantity = params.get('quantity', quantity)

        # Read the current level of allAvailableResources
        resources = await exposed_thing.read_property('allAvailableResources')
        
        # Calculate the new level of resources
        newResources = resources.copy()
        newResources['water'] -= math.ceil(quantity * sizeQuantifiers[size] * drinkRecipes[drinkId]['water'])
        newResources['milk'] -= math.ceil(quantity * sizeQuantifiers[size] * drinkRecipes[drinkId]['milk'])
        newResources['chocolate'] -= math.ceil(quantity * sizeQuantifiers[size] * drinkRecipes[drinkId]['chocolate'])
        newResources['coffeeBeans'] -= math.ceil(quantity * sizeQuantifiers[size] * drinkRecipes[drinkId]['coffeeBeans'])
        
        # Check if the amount of available resources is sufficient to make a drink
        for resource, value in six.iteritems(newResources):
            if value <= 0:
                # Emit outOfResource event
                exposed_thing.emit_event('outOfResource', f'Low level of {resource}: {resources[resource]}%')
                return {'result': False, 'message': f'{resource} level is not sufficient'}
        
        # Now store the new level of allAvailableResources and servedCounter
        await exposed_thing.properties['allAvailableResources'].write(newResources)

        servedCounter = await exposed_thing.read_property('servedCounter')
        servedCounter += quantity
        await exposed_thing.properties['servedCounter'].write(servedCounter)

        # Finally deliver the drink
        return {'result': True, 'message': f'Your {drinkId} is in progress!'}

    exposed_thing.set_action_handler('makeDrink', make_drink_action_handler)

    # Set up a handler for setSchedule action
    async def set_schedule_action_handler(params):
        params = params['input'] if params['input'] else {}

        # Check if required fields are provided in input
        if 'time' in params and 'mode' in params:
            
            # Use default values for non-required fields if not provided
            params['drinkId'] = params.get('drinkId', 'americano')
            params['size'] = params.get('size', 'm')
            params['quantity'] = params.get('quantity', 1)

            # Now read the schedules property, add a new schedule to it and then rewrite the schedules property
            schedules = await exposed_thing.read_property('schedules')
            schedules.append(params)
            await exposed_thing.properties['schedules'].write(schedules)
            return {'result': True, 'message': 'Your schedule has been set!'}
        
        return {'result': False, 'message': 'Please provide all the required parameters: time and mode.'}

    exposed_thing.set_action_handler('setSchedule', set_schedule_action_handler)

    exposed_thing.expose()
    LOGGER.info(f"{TD['title']} is ready")


def read_from_sensor(sensorType):
    # Actual implementation of reading data from a sensor can go here
    # For the sake of example, let's just return a value
    return 100


def notify(msg, subscribers=['admin@coffeeMachine.com']):
    # Actual implementation of notifying subscribers with a message can go here
    LOGGER.info(msg)


if __name__ == "__main__":
    LOGGER.info("Starting loop")
    IOLoop.current().add_callback(main)
    IOLoop.current().start()
