"""
In this file we specify default event handlers which are then populated into the handler map using metaprogramming
Copyright Anjishnu Kumar 2015
Happy Hacking!
"""

import json
import logging
import os
import urllib
import requests
from ask import alexa
from ncs.osph_metric_io import MetricData

__version__ = "1.0"


def lambda_handler(request_obj, context=None):
    '''
    This is the main function to enter to enter into this code.
    If you are hosting this code on AWS Lambda, this should be the entry point.
    Otherwise your server can hit this code as long as you remember that the
    input 'request_obj' is JSON request converted into a nested python object.
    '''

    # Setup configuration vars from lambda environment (lazy code)
    api_base = os.environ['api_base']
    user_name = os.environ['user']
    password = os.environ['password']
    skill_id = os.environ['skill_id']
    event_session = None   # event['session']

    # Get session ID
    session_token = create_ns_session(api_base, user_name, password, event_session)
    logging.debug("create_ns_session: token = %s", session_token)
    logging.debug("create_ns_session: api_base = %s", api_base)

    metadata = {'user_name': user_name,
                'password': password,
                'api_base': api_base,
                'token': session_token,
                'skill_id': skill_id}

    ''' inject user relevant metadata into the request if you want to, here.    
    e.g. Something like : 
    ... metadata = {'user_name' : some_database.query_user_name(request.get_user_id())}

    Then in the handler function you can do something like -
    ... return alexa.create_response('Hello there {}!'.format(request.metadata['user_name']))
    '''
    return alexa.route_request(request_obj, metadata)


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

# --------------- Decorated functions for the route handlers ----------------------


# default_handler = alexa.default_handler(default_handler)
@alexa.default_handler()
def default_handler(request):
    """ The default handler gets invoked if no handler is set for a request """
    return alexa.create_response(message="Just ask")


# syntactic sugar
# launch_request_handler = alexa.request_handler("LaunchRequest")
# Welcome message when no intent is given
@alexa.request_handler("LaunchRequest")
def launch_request_handler(request):
    return alexa.create_response(message="Welcome to the OneSphere voice activated cloud management console. " +
                                         "Please ask me something about your OneSphere service")


# Message when receiving an end session intent
@alexa.request_handler("SessionEndedRequest")
def session_ended_request_handler(request):
    return alexa.create_response(
        message="Thank you for trying the OneSphere voice activated cloud management console. " +
                "Have a nice day! ")


# Message when receiving a brohug intent
@alexa.intent_handler("BroHugDistance")
def get_brohug_intent_handler(request):

    card = alexa.create_card(title="GetBroHugIntent activated", subtitle=None,
                             content="asked alexa to give BroHug advice")

    return alexa.create_response(
        message="You must remember to maintain a safe groin distance of 1 foot " +
                "when executing a proper bro hug.",
        end_session=False, card_obj=card)


@alexa.intent_handler('ServiceStatus')
def get_service_intent_handler(request):
    """
    Query the OneSphere status API and return the service status.
    """

    # Get KMS secured environment variables
    api_base = request.metadata.get('api_base', None)

    # Get service status
    r = safe_requests(requests.get, api_base + "/status")

    if 'service' in r:
        speech_output = "The OneSphere service is currently " + r["service"]
    else:
        speech_output = "The OneSphere service is currently unavailable"

    card = alexa.create_card(title="GetServiceStatusIntent activated", subtitle=None,
                             content="asked alexa to query the OneSphere service status REST API")

    return alexa.create_response(speech_output,end_session=False, card_obj=card)


@alexa.intent_handler('TotalMonSpend')
def get_tot_mon_spend_handler(request):
    """ Queries the OneSphere metrics API and returns the total current month spend.
    """

    # Get KMS secured environment variables
    api_base = request.metadata.get('api_base', None)
    token = request.metadata.get('token', None)

    # Get service status
    # periodStart should default to the current month
    # 'periodStart': '2018-01-01T00:00:00Z',
    payload = {'category': 'providers', 'name': 'cost.total',
               'period': 'month', 'periodCount': '-1', 'view': 'full'}
    r = safe_requests(requests.get, api_base + "/metrics", params=payload,
                      headers={'accept': 'application/json',
                               'Content-Type': 'application/json',
                               'Authorization': token}
                      )

    # Parse metrics JSON output
    metric_data = MetricData(r)
    total_spend = metric_data.get_cost()
    speech_output = "The OneSphere service spend for this month is ${:,.2f}".format(total_spend)

    card = alexa.create_card(title="GetTotMonSpendIntent activated", subtitle=None,
                             content="asked alexa to query the OneSphere metrics REST API and calculate"\
                             " the total monthly spend")

    return alexa.create_response(speech_output,end_session=False, card_obj=card)


@alexa.intent_handler('OnpremCurrentMonSpend')
def get_onprem_spend_handler(request):
    """ Queries the OneSphere metrics API and returns the total current month spend.
    """

    # Get KMS secured environment variables
    api_base = request.metadata.get('api_base', None)
    token = request.metadata.get('token', None)

    # Get service status
    # periodStart should default to the current month
    # 'periodStart': '2018-01-01T00:00:00Z',
    payload = {'category': 'providers', 'query': 'providerTypeUri EQ /rest/provider-types/ncs',
               'name': 'cost.usage', 'period': 'month', 'periodCount': '-1', 'view': 'full'
               }
    params = urllib.urlencode(payload)
    r = safe_requests(requests.get, api_base + "/metrics", params=params,
                      headers={'accept': 'application/json;charset=UTF-8',
                               'Authorization': token}
                      )

    # Parse metrics JSON output
    metric_data = MetricData(r)
    total_spend = metric_data.get_cost()
    speech_output = "The OneSphere service private cloud spend for this month is ${:,.2f}".format(total_spend)

    card = alexa.create_card(title="GetOnpremSpendIntent activated", subtitle=None,
                             content="asked alexa to query the OneSphere metrics REST API and calculate" \
                                     " the total private cloud monthly spend")

    return alexa.create_response(speech_output,end_session=False, card_obj=card)


@alexa.intent_handler('OnPremCostSavings')
def get_onprem_cost_savings_handler(request):
    """ Queries the OneSphere metrics API and returns the total private cloud cost savings.
        NOT YET IMPLEMENTED
    """

    speech_output = "The OneSphere service private cloud cost savings feature is not yet implemented"

    card = alexa.create_card(title="GetOnpremCostSavingsIntent activated", subtitle=None,
                             content="asked alexa to query the OneSphere metrics REST API and calculate" \
                                     " the total private cloud monthly cost savings")

    return alexa.create_response(speech_output,end_session=False, card_obj=card)


@alexa.intent_handler('AWSNCSManagedUtil')
def get_onprem_cost_efficiency_handler(request):
    """ Queries the OneSphere metrics API and returns the  private cloud cost efficiency.
    """

    # Get KMS secured environment variables
    api_base = request.metadata.get('api_base', None)
    token = request.metadata.get('token', None)

    # Get service status
    # periodStart should default to the current month
    # 'periodStart': '2018-01-01T00:00:00Z',
    payload = {'category': 'providers', 'groupBy': 'providerTypeUri',
               'name': 'cost.efficiency', 'period': 'month', 'periodCount': '-1', 'view': 'full'
               }
    r = safe_requests(requests.get, api_base + "/metrics", params=payload,
                      headers={'accept': 'application/json',
                               'Authorization': token}
                      )

    # Parse metrics JSON output
    metric_data = MetricData(r)
    total_spend = metric_data.get_cost()
    speech_output = "The OneSphere service private cloud efficiency for this month is ${:,.2f}".format(total_spend)

    card = alexa.create_card(title="GetOnpremCostEfficiencyIntent activated", subtitle=None,
                             content="asked alexa to query the OneSphere metrics REST API and calculate" \
                                     " the total private cloud monthly cost efficiency")

    return alexa.create_response(speech_output,end_session=False, card_obj=card)


if __name__ == "__main__":

    # open test json event
    event = json.load(open('test-data/event.json'))
    cred = json.load(open('keys/cred.json'))

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
