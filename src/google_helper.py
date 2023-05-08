import src.logging_helper as logging

from googleapiclient.discovery import build
import configparser
import os

config = configparser.ConfigParser(os.environ)
config_path = os.path.dirname(__file__) + '/../config/' #we need this trick to get path to config folder
config.read(config_path + 'settings.ini')

def google_search(search_term, api_key = config['GOOGLE']['KEY'], cse_id = config['GOOGLE']['CSE_ID'], **kwargs):
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()

    if 'items' in res:
        return res['items']
    else:
        return None
