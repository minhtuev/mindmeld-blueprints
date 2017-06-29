# -*- coding: utf-8 -*-
"""This module contains the Workbench home assistant blueprint application"""
from __future__ import unicode_literals
from mmworkbench import Application
import requests
import os

app = Application(__name__)

# Weather constants
CITY_NOT_FOUND_CODE = '404'
INVALID_API_KEY_CODE = '401'
DEFAULT_TEMPERATURE_UNIT = 'Fahrenheit'
DEFAULT_LOCATION = 'San Francisco'
OPENWEATHER_BASE_STRING = 'http://api.openweathermap.org/data/2.5/weather'

DEFAULT_THERMOSTAT_TEMPERATURE = 72
DEFAULT_THERMOSTAT_LOCATION = 'home'
DEFAULT_HOUSE_LOCATION = None
DEFAULT_TEMPERATURE_CHANGE = None


@app.handle(intent='check-weather')
def check_weather(context, slots, responder):
    """
    When the user asks for weather, return the weather in that location or use San Francisco if no
      location is given.
    """
    # Check to make sure API key is present, if not tell them to follow setup instructions
    try:
        openweather_api_key = os.environ['OPEN_WEATHER_KEY']
    except KeyError:
        reply = "Open weather API is not setup, please follow instructions to setup the API."
        responder.reply(reply)
        return

    # Get the location the user wants
    selected_city = _get_city(context)
    # Figure out which temperature unit the user wants information in
    selected_unit = _get_unit(context)

    # Get weather information via the API
    url_string = _construct_weather_api_url(selected_city, selected_unit, openweather_api_key)
    try:
        weather_info = requests.get(url_string).json()
    except ConnectionError:
        reply = "Sorry, I was unable to connect to the weather API, please check your connection."
        responder.reply(reply)
        return

    if weather_info['cod'] == CITY_NOT_FOUND_CODE:
        reply = "Sorry, I wasn't able to recognize that city."
        responder.reply(reply)
    elif weather_info['cod'] == INVALID_API_KEY_CODE:
        reply = "Sorry, the API key is invalid."
        responder.reply(reply)
    else:
        slots['city'] = weather_info['name']
        slots['temp_min'] = weather_info['main']['temp_min']
        slots['temp_max'] = weather_info['main']['temp_max']
        slots['condition'] = weather_info['weather'][0]['main']
        responder.reply("The weather in {city} is {condition} with a min of {temp_min} and a max of"
                        " {temp_max}")


@app.handle(intent='specify-location')
def specify_location(context, slots, responder):

    selected_all = False
    selected_location = _get_location(context)

    if context['frame']['desired_action'] == 'Close Door':
        reply = _handle_door_reply(selected_all, selected_location, desired_state="closed")
    elif context['frame']['desired_action'] == 'Open Door':
        reply = _handle_door_reply(selected_all, selected_location, desired_state="opened")
    elif context['frame']['desired_action'] == 'Lock Door':
        reply = _handle_door_reply(selected_all, selected_location, desired_state="locked")
    elif context['frame']['desired_action'] == 'Unlock Door':
        reply = _handle_door_reply(selected_all, selected_location, desired_state="unlocked")
    elif context['frame']['desired_action'] == 'Turn On Lights':
        reply = _handle_lights_reply(selected_all, selected_location, desired_state="on")
    elif context['frame']['desired_action'] == 'Turn Off Lights':
        reply = _handle_lights_reply(selected_all, selected_location, desired_state="off")
    elif context['frame']['desired_action'] == 'Turn On Appliance':
        selected_appliance = context['frame']['appliance']
        reply = _handle_appliance_reply(selected_location, selected_appliance, desired_state="on")
    elif context['frame']['desired_action'] == 'Turn Off Appliance':
        selected_appliance = context['frame']['appliance']
        reply = _handle_appliance_reply(selected_location, selected_appliance, desired_state="off")

    responder.reply(reply)


@app.handle(intent='specify-temperature')
def specify_temperature(context, slots, responder):

    selected_temperature_amount = _get_temperature(context)
    selected_location = context['frame']['thermostat_location']

    thermostat_temperature_dict = context['request']['session']['thermostat_temperatures']

    if context['frame']['desired_action'] == 'Set Thermostat':
        thermostat_temperature_dict[selected_location] = selected_temperature_amount
        reply = _handle_thermostat_change_reply(selected_location,
                                                desired_temperature=selected_temperature_amount)
    elif context['frame']['desired_action'] == 'Turn Up Thermostat':
        thermostat_temperature_dict[selected_location] += selected_temperature_amount

        new_temperature = thermostat_temperature_dict[selected_location]
        reply = _handle_thermostat_change_reply(selected_location,
                                                desired_temperature=new_temperature)
    elif context['frame']['desired_action'] == 'Turn Down Thermostat':
        thermostat_temperature_dict[selected_location] -= selected_temperature_amount

        new_temperature = thermostat_temperature_dict[selected_location]
        reply = _handle_thermostat_change_reply(selected_location,
                                                desired_temperature=new_temperature)

    responder.reply(reply)


@app.handle(intent='close-door')
def close_door(context, slots, responder):

    selected_all = _get_command_for_all(context)
    selected_location = _get_location(context)

    if selected_all or selected_location:
        reply = _handle_door_reply(selected_all, selected_location, desired_state="closed")
        responder.reply(reply)
    else:
        context['frame']['desired_action'] = 'Close Door'
        prompt = "Of course, which door?"
        responder.prompt(prompt)


@app.handle(intent='open-door')
def open_door(context, slots, responder):

    selected_all = _get_command_for_all(context)
    selected_location = _get_location(context)

    if selected_all or selected_location:
        reply = _handle_door_reply(selected_all, selected_location, desired_state="opened")
        responder.reply(reply)
    else:
        context['frame']['desired_action'] = 'Open Door'
        prompt = "Of course, which door?"
        responder.prompt(prompt)


@app.handle(intent='lock-door')
def lock_door(context, slots, responder):

    selected_all = _get_command_for_all(context)
    selected_location = _get_location(context)

    if selected_all or selected_location:
        reply = _handle_door_reply(selected_all, selected_location, desired_state="locked")
        responder.reply(reply)
    else:
        context['frame']['desired_action'] = 'Lock Door'
        prompt = "Of course, which door?"
        responder.prompt(prompt)


@app.handle(intent='unlock-door')
def unlock_door(context, slots, responder):

    selected_all = _get_command_for_all(context)
    selected_location = _get_location(context)

    if selected_all or selected_location:
        reply = _handle_door_reply(selected_all, selected_location, desired_state="unlocked")
        responder.reply(reply)
    else:
        context['frame']['desired_action'] = 'Unlock Door'
        prompt = "Of course, which door?"
        responder.prompt(prompt)


@app.handle(intent='turn-appliance-on')
def turn_appliance_on(context, slots, responder):

    selected_location = _get_location(context)
    selected_appliance = _get_appliance(context)

    if selected_location:
        reply = _handle_appliance_reply(selected_location, selected_appliance, desired_state="on")
        responder.reply(reply)
    else:
        context['frame']['desired_action'] = 'Turn On'
        context['frame']['appliance'] = selected_appliance

        prompt = "Of course, which {appliance}".format(appliance=selected_appliance)
        responder.prompt(prompt)


@app.handle(intent='turn-appliance-off')
def turn_appliance_off(context, slots, responder):

    selected_location = _get_location(context)
    selected_appliance = _get_appliance(context)

    if selected_location:
        reply = _handle_appliance_reply(selected_location, selected_appliance, desired_state="off")
        responder.reply(reply)
    else:
        context['frame']['desired_action'] = 'Turn Off'
        context['frame']['appliance'] = selected_appliance

        prompt = "Of course, which {appliance}".format(appliance=selected_appliance)
        responder.prompt(prompt)


@app.handle(intent='turn-lights-on')
def turn_lights_on(context, slots, responder):

    selected_all = _get_command_for_all(context)
    selected_location = _get_location(context)

    if selected_all or selected_location:
        reply = _handle_lights_reply(selected_all, selected_location, desired_state="on")
        responder.reply(reply)
    else:
        context['frame']['desired_action'] = 'Turn On Lights'
        prompt = "Of course, which lights?"
        responder.prompt(prompt)


@app.handle(intent='turn-lights-off')
def turn_lights_off(context, slots, responder):

    selected_all = _get_command_for_all(context)
    selected_location = _get_location(context)

    if selected_all or selected_location:
        reply = _handle_lights_reply(selected_all, selected_location, desired_state="off")
        responder.reply(reply)
    else:
        context['frame']['desired_action'] = 'Turn Off Lights'
        prompt = "Of course, which lights?"
        responder.prompt(prompt)


@app.handle(intent='check-thermostat')
def check_thermostat(context, slots, responder):

    selected_location = _get_thermostat_location(context)

    try:
        current_temp = context['request']['session']['thermostat_temperatures'][selected_location]
    except KeyError:
        current_temp = DEFAULT_THERMOSTAT_TEMPERATURE
        context['request']['session']['thermostat_temperatures'] = {selected_location, current_temp}

    reply = "Current thermostat temperature in the {location} is {temp}.".format(
        location=selected_location.lower(), temp=current_temp)
    responder.reply(reply)


@app.handle(intent='set-thermostat')
def set_thermostat(context, slots, responder):

    selected_location = _get_thermostat_location(context)
    selected_temperature = _get_temperature(context)

    thermostat_temperature_dict = context['request']['session']['thermostat_temperatures']

    if selected_temperature:
        thermostat_temperature_dict[selected_location] = selected_temperature
        reply = _handle_thermostat_change_reply(selected_location,
                                                desired_temperature=selected_temperature)
        responder.reply(reply)
    else:
        context['frame']['desired_action'] = "Set Thermostat"
        prompt = "Of course, what temperature shall I set it to?"
        responder.prompt(prompt)


@app.handle(intent='turn-down-thermostat')
def turn_down_thermostat(context, slots, responder):

    selected_location = _get_thermostat_location(context)
    selected_temperature_amount = _get_temperature(context)

    thermostat_temperature_dict = context['request']['session']['thermostat_temperatures']

    if selected_temperature_amount:
        thermostat_temperature_dict[selected_location] -= selected_temperature_amount
        new_temperature = thermostat_temperature_dict[selected_location]

        reply = _handle_thermostat_change_reply(selected_location,
                                                desired_temperature=new_temperature)
        responder.reply(reply)
    else:
        context['frame']['desired_action'] = "Turn Down Thermostat"
        context['frame']['thermostat_location'] = selected_location
        prompt = "Of course, by how much?"
        responder.prompt(prompt)


@app.handle(intent='turn-up-thermostat')
def turn_up_thermostat(context, slots, responder):

    selected_location = _get_thermostat_location(context)
    selected_temperature_amount = _get_temperature(context)

    thermostat_temperature_dict = context['request']['session']['thermostat_temperatures']

    if selected_temperature_amount:
        thermostat_temperature_dict[selected_location] += selected_temperature_amount
        new_temperature = thermostat_temperature_dict[selected_location]

        reply = _handle_thermostat_change_reply(selected_location,
                                                desired_temperature=new_temperature)
        responder.reply(reply)
    else:
        context['frame']['desired_action'] = "Turn Up Thermostat"
        prompt = "Of course, by how much?"
        responder.prompt(prompt)


@app.handle(intent='turn-off-thermostat')
def turn_off_thermostat(context, slots, responder):

    selected_location = _get_thermostat_location(context)
    reply = _handle_thermostat_change_reply(selected_location, desired_state='off')
    responder.reply(reply)


@app.handle(intent='turn-on-thermostat')
def turn_on_thermostat(context, slots, responder):

    selected_location = _get_thermostat_location(context)
    reply = _handle_thermostat_change_reply(selected_location, desired_state='on')
    responder.reply(reply)


@app.handle(intent='unsupported')
@app.handle()
def default(context, slots, responder):
    prompts = ["Sorry, not sure what you meant there."]
    responder.prompt(prompts)


# Helper Functions


def _construct_weather_api_url(selected_location, selected_unit, openweather_api_key):
    unit_string = 'metric' if selected_unit == 'Celsius' else 'imperial'
    url_string = "{base_string}?q={location}&units={unit}&appid={key}".format(
        base_string=OPENWEATHER_BASE_STRING, location=selected_location.replace(" ", "+"),
        unit=unit_string, key=openweather_api_key)

    return url_string


def _kb_fetch(kb_index, kb_id):
    """
    Retrieve the detailed knowledge base entry for a given ID from the specified index.

    Args:
        index (str): The knowledge base index to query
        id (str): Identifier for a specific entry in the index

    Returns:
        dict: The full knowledge base entry corresponding to the given ID.
    """
    return app.question_answerer.get(index=kb_index, id=kb_id)[0]


# Reply handlers

def _handle_lights_reply(selected_all, selected_location, desired_state):

    if selected_all:
        reply = "Ok. All lights have been turned {state}.".format(state=desired_state)
    elif selected_location:
        reply = "Ok. The {location} lights have been turned {state}.".format(
            location=selected_location.lower(), state=desired_state)

    return reply


def _handle_door_reply(selected_all, selected_location, desired_state):

    if selected_all:
        reply = "Ok. All doors have been {state}.".format(state=desired_state)
    elif selected_location:
        reply = "Ok. The {location} door has been {state}.".format(
            location=selected_location.lower(), state=desired_state)

    return reply


def _handle_appliance_reply(selected_location, selected_appliance, desired_state):

    reply = "Ok. The {appliance} has been turned {state}.".format(appliance=selected_appliance,
                                                                  state=desired_state)
    return reply


def _handle_thermostat_change_reply(selected_location, desired_temperature=None,
                                    desired_state=None):

    if desired_temperature:
        reply = "The thermostat temperature in the {location} is now {temp} degrees F.".format(
            location=selected_location, temp=desired_temperature)
    elif desired_state:
        reply = "Ok. The thermostat in the {location} has been turned {state}.".format(
            location=selected_location, state=desired_state)

    return reply


# Entity Resolvers

def _get_location(context):
    """
    Get's the user desired location within house from the query

    Args:
        context (dict): contains info about the conversation up to this point
        (e.g. domain, intent, entities, etc)

    Returns:
        string: resolved location entity
    """
    location_entity = next((e for e in context['entities'] if e['type'] == 'location'), None)

    if location_entity:
        return _kb_fetch('locations', location_entity['value'][0]['id'])
    else:
        # Default to Fahrenheit
        return DEFAULT_HOUSE_LOCATION


def _get_command_for_all(context):
    """
    Looks at user query to see if user wants all the lights or all the doors turned off

    Args:
        context (dict): contains info about the conversation up to this point
        (e.g. domain, intent, entities, etc)

    Returns:
        bool: whether or not the user made a command for all
    """
    all_entity = next((e for e in context['entities'] if e['type'] == 'all'), None)

    if all_entity:
        return True
    else:
        return False


def _get_appliance(context):
    """
    Get's the user target appliance, should always detect something

    Args:
        context (dict): contains info about the conversation up to this point
        (e.g. domain, intent, entities, etc)

    Returns:
        string: resolved appliance entity
    """
    appliance_entity = next((e for e in context['entities'] if e['type'] == 'appliance'), None)

    if appliance_entity:
        return _kb_fetch('appliances', appliance_entity['value'][0]['id'])
    else:
        raise Exception("There should always be a recognizable appliance if we go down this intent")


def _get_thermostat_location(context):
    """
    Get's the user desired thermostat location within house from the query, defaults to 'home'

    Args:
        context (dict): contains info about the conversation up to this point
        (e.g. domain, intent, entities, etc)

    Returns:
        string: resolved location entity, 'home' if no resolution
    """
    location_entity = next((e for e in context['entities'] if e['type'] == 'location'), None)

    if location_entity:
        return _kb_fetch('locations', location_entity['value'][0]['id'])
    else:
        return DEFAULT_THERMOSTAT_LOCATION


def _get_temperature(context):
    """
    Get's the user desired temperature or temperature change

    Args:
        context (dict): contains info about the conversation up to this point
        (e.g. domain, intent, entities, etc)

    Returns:
        string: resolved temperature entity
    """
    temperature_entity = next((e for e in context['entities'] if e['type'] == 'temperature'), None)

    if temperature_entity:
        return _kb_fetch('temperatures', temperature_entity['value'][0]['id'])
    else:
        return DEFAULT_TEMPERATURE_CHANGE


def _get_unit(context):
    """
    Get's the user desired temperature unit from the query, defaulting to Fahrenheit if none
      is provided

    Args:
        context (dict): contains info about the conversation up to this point (e.g. domain, intent,
          entities, etc)

    Returns:
        string: resolved temperature unit entity
    """
    unit_entity = next((e for e in context['entities'] if e['type'] == 'unit'), None)

    if unit_entity:
        return _kb_fetch('units', unit_entity['value'][0]['id'])
    else:
        # Default to Fahrenheit
        return DEFAULT_TEMPERATURE_UNIT


def _get_city(context):
    """
    Get's the user location from the query, defaulting to San Francisco if none provided

    Args:
        context (dict): contains info about the conversation up to this point (e.g. domain, intent,
          entities, etc)

    Returns:
        string: resolved location entity
    """
    location_entity = next((e for e in context['entities'] if e['type'] == 'city'), None)

    if location_entity:
        return _kb_fetch('cities', id=location_entity['value'][0]['id'])
    else:
        # Default to San Francisco
        return DEFAULT_LOCATION


if __name__ == '__main__':
    app.cli()
