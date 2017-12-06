"""
This is a voice activated console for OneSphere
"""

from __future__ import print_function
import requests
import logging
import json
import os

__version__ = "1.0"

# Global vars taken from environment variables
API_BASE = ""
USER = ""
PASSWORD = ""
TOKEN = ""

# --------------- Helpers that build all of the responses ----------------------


def safe_requests(f, *args, **kwargs):
    """ A helper function to wrap requests calls with try/except block
    """
    try:

        r = f(*args, **kwargs)

        if r.status_code != 200:
            logging.error("Error: Unexpected response {}".format(r))
            return {}
        else:
            return r.json()

    except requests.exceptions.RequestException as e:
        logging.error("Error: {}".format(e))
        return {}


def create_ns_session(api_base, user_name, password, session_id):
    """ A helper function which creates a session with OneSphere. Rely on
    environment variables for userName and password.
    """

    # Get session key
    payload = {'userName': user_name, 'password': password}

    r = safe_requests(requests.post, api_base + "/session",
                      data=json.dumps(payload),
                      headers={'accept': 'application/json', 'Content-Type': 'application/json'}
                      )

    if 'token' in r:
        return r['token']
    else:
        return ""


def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': __version__,
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to the OneSphere voice activated cloud management console. " \
                    "Please ask me something about your OneSphere service"
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Please ask me something about your OneSphere service"
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for trying the OneSphere voice activated cloud management console. " \
                    "Have a nice day! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


def return_brohug_advice(intent, session):
    """ Return sage brohug advice for the brohug novice
    """

    session_attributes = {}
    card_title = "BrohugAdvice"
    speech_output = "You must remember to maintain a safe groin distance of 1 foot " \
                    "when executing a proper bro hug."
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Feel free to ask me another question about OneSphere"
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def return_service_status(intent, session):
    """ Queries the OneSphere status API and returns the service status.
    """

    # Get KMS secured environment variables
    api_base = API_BASE

    card_title = intent['name']
    session_attributes = {}
    should_end_session = False
    reprompt_text = ""

    # Get service status
    r = safe_requests(requests.get, api_base + "/status")

    if 'service' in r:
        speech_output = "The OneSphere service is currently " + r["service"]
    else:
        speech_output = "The OneSphere service is currently unavailable"

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def return_total_mon_spend(intent, session):
    """ Queries the OneSphere metrics API and returns the total current month spend.
    """

    # Get KMS secured environment variables
    api_base = API_BASE
    token = TOKEN

    card_title = intent['name']
    session_attributes = {}
    should_end_session = False
    reprompt_text = ""

    # Get service status
    payload = {'category': 'providers', 'name': 'cost.total',
               'periodStart': '2018-01-01T00:00:00Z',
               'period': 'month', 'periodCount': '-1', 'view': 'full'}
    r = safe_requests(requests.get, api_base + "/metrics", params=payload,
                      headers={'accept': 'application/json',
                               'Content-Type': 'application/json',
                               'Authorization': token}
                      )

    # Check json returned
    if 'total' in r:
        # Iterate on number of records
        num_records = int(r['total'])
        total_spend = 0
        for i in range(0, num_records):
            member = r["members"][i]
            value = member["values"][0]
            val = value["value"]
            logging.debug("value = %d", val)
            total_spend = total_spend + val

        # Create response
        speech_output = "The OneSphere service spend for this month is ${:,.2f}".format(total_spend)
    else:
        speech_output = "The OneSphere service did not respond correctly"

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


# --------------- Events ------------------


def on_session_started(session_started_request, session):
    """ Called when the session starts """

    logging.info("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    logging.info("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    logging.info("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "ServiceStatus":
        return return_service_status(intent, session)
    elif intent_name == "TotalMonSpend":
        return return_total_mon_spend(intent, session)
    elif intent_name == "BroHugDistance":
        return return_brohug_advice(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    logging.info("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """

    logging.info("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    # Validate the application ID
    if (event['session']['application']['applicationId'] !=
            os.environ['skill_id']):
        raise ValueError("Invalid Application ID")

    # Setup global vars from lambda environment (lazy code)
    global API_BASE
    global USER
    global PASSWORD
    API_BASE = os.environ['api_base']
    USER = os.environ['user']
    PASSWORD = os.environ['password']

    # Get session ID
    global TOKEN
    TOKEN = create_ns_session(API_BASE, USER, PASSWORD, event['session'])
    logging.debug("create_ns_session: token = %s", TOKEN)
    logging.debug("create_ns_session: api_base = %s", API_BASE)

    # Select the appropriate event handler
    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])


if __name__ == "__main__":

    # open test json event
    event = json.load(open('event.json'))
    cred = json.load(open('cred.json'))

    # set logging level
    logging.basicConfig(level=logging.INFO)

    # unit test harness
    os.environ['api_base'] = cred["api_base"]
    os.environ['skill_id'] = "foobar"
    os.environ['user'] = cred["userName"]
    os.environ['password'] = cred["password"]
    context = ""
    logging.info(os.environ)
    logging.info(lambda_handler(event, context))
