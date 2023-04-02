import os
import configparser
import requests
import logging

config = configparser.ConfigParser(os.environ)
config_path = os.path.dirname(__file__) + '/../config/' #we need this trick to get path to config folder
config.read(config_path + 'settings.ini')

class TelegramLoggerHandler(logging.Handler):
    def __init__(self):
        super().__init__()

    def emit(self, record):
        # OVERWRITE LOG METHOD WITH OUR TELEGRAM LOGIC
        # TODO:LOW: maybe it's better to rewrite this with bot.send_message
        URL = f"https://api.telegram.org/bot{config['TELEGRAM']['KEY']}/sendMessage?chat_id={config['TELEGRAM']['ADMIN_ID']}&text={record}"

        r = requests.get(url=URL)
        data = r.json()

        # TODO:LOW: check if we need to call original emit method
        # super().emit(record)

def get_logger():
    logger = logging.getLogger()
    if config['LOGGING']['LEVEL'] == 'DEBUG':
        logger.setLevel(logging.DEBUG)
    elif config['LOGGING']['LEVEL'] == 'INFO':
        logger.setLevel(logging.INFO)
    elif config['LOGGING']['LEVEL'] == 'WARNING':
        logger.setLevel(logging.WARNING)
    elif config['LOGGING']['LEVEL'] == 'ERROR':
        logger.setLevel(logging.ERROR)
    elif config['LOGGING']['LEVEL'] == 'CRITICAL':
        logger.setLevel(logging.CRITICAL)
    handler = TelegramLoggerHandler()
    # formatter = logging.Formatter(config['LOGGING']['FORMAT'])
    # handler.setFormatter(formatter)
    if (logger.hasHandlers()):
        logger.handlers.clear()
    logger.addHandler(handler)

    return logger