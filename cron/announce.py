import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
import configparser
import os

# Import process_message_queue from your main script
import src.db_helper as db_helper
import src.announce_helper as announce_helper

config = configparser.ConfigParser(os.environ)
config_path = os.path.dirname(__file__) + '/../config/'
config.read(config_path + 'settings.ini')

client = TelegramClient(StringSession(config['TELEGRAM']['SESSION_STRING']), config['TELEGRAM']['API_ID'], config['TELEGRAM']['API_HASH'])

async def main():
    await client.start()

    with db_helper.session_scope() as session:

        # Adjust the batch size and delay as needed
        messages_to_send = config['ANNOUNCE']['MESSAGES_TO_SEND']
        delay_between_messages = int(config['ANNOUNCE']['DELAY_BETWEEN_MESSAGES'])

        await announce_helper.process_message_queue(client, messages_to_send, delay_between_messages, session)

    await client.disconnect()


if __name__ == '__main__':
    asyncio.run(main())