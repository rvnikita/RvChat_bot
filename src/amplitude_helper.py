import os
import configparser
from amplitude import Amplitude, BaseEvent

config = configparser.ConfigParser(os.environ)
config_path = os.path.dirname(__file__) + '/../config/' #we need this trick to get path to config folder
config.read(config_path + 'settings.ini')


amplitude = Amplitude(config['AMPLITUDE']['API_KEY'])

def track(user_id, event_type = None, event_properties = None):
    if event_type is None:
        event_type = "/default"

    amplitude.track(
        BaseEvent(
            user_id=str(user_id),
            event_type = str(event_type),
            event_properties=event_properties
        )
    )