import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = os.environ['API_ID']
API_HASH = os.environ['API_HASH']
PHONE_NUMBER = os.environ['PHONE_NUMBER']
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

client = TelegramClient('my_user_account', API_ID, API_HASH)

async def generate_session_string():
    # Initialize the Telegram client
    # Connect and sign in using the phone number
    # await client.start(PHONE_NUMBER)
    # await client.send_message(88834504, "Hello world")

    async with TelegramClient(StringSession(), API_ID, API_HASH) as client2:
        print(client2.session.save())

if __name__ == '__main__':
    session_string = client.loop.run_until_complete(generate_session_string())
    print(session_string)