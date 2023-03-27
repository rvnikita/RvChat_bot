import src.db_helper as db_helper

import os
from telethon import TelegramClient, events, types
from telethon.sessions import StringSession
import openai
import json

#TODO:HIGH: move env variables to .env file
# Get API credentials from environment variables
API_ID = os.environ['API_ID']
API_HASH = os.environ['API_HASH']
PHONE_NUMBER = os.environ['PHONE_NUMBER']
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
TELEGRAM_SESSION_STRING = os.environ['TELEGRAM_SESSION_STRING']
#TODO:MED: rewrite this with logging module
LOGGING_CHAT_ID = int(os.environ['LOGGING_CHAT_ID'])

openai.api_key = OPENAI_API_KEY
client = TelegramClient(StringSession(TELEGRAM_SESSION_STRING), API_ID, API_HASH)

async def generate_response(conversation_history, preprompt = None):
    me = await client.get_me()

    prompt = []

    if preprompt:
        prompt.append({"role": "system", "content": preprompt})

    #loop through the conversation history
    for message in conversation_history:
        if message.sender == me: #from bot
            prompt.append({"role": "assistant", "content": message.text})
        else:
            prompt.append({"role": "user", "content": message.text})

    # temporary log to admin
    await client.send_message(LOGGING_CHAT_ID, json.dumps(prompt, indent=4))

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=prompt
    )

    reply_text = response.choices[0].message.content.strip()
    return reply_text

async def get_last_x_messages(client, channel_id, max_tokens = 4000):
    channel = await client.get_entity(channel_id)

    # Fetch messages until '/clear' or until max tokens
    messages = []
    total_tokens = 0
    min_id = None

    async for msg in client.iter_messages(channel):
        if msg.text == '/clear' or msg.text == 'Clearing conversation history':
            break

        if total_tokens + len(msg.text) <= max_tokens:
            messages.append(msg)
            total_tokens += len(msg.text)
            min_id = msg.id
        else:
            break

    return messages[::-1]

async def on_new_message(event):
    try:
        if event.chat_id != 88834504 and event.chat_id != 200204708:
            # For now debug only on my account
            return
        elif event.text == '/clear':
            await client.send_message(event.chat_id, "Clearing conversation history")
            return

        async with client.action(event.chat_id, 'typing'):
            conversation_history = await get_last_x_messages(client, event.chat_id, 500)

            #select preprompt form db for this user
            user = db_helper.session.query(db_helper.User).filter_by(id=event.sender_id).first()
            if user is None:
                user = db_helper.User(id=event.chat_id, status='active', preprompt='')
                db_helper.session.add(user)
                db_helper.session.commit()

                preprompt = None
            else:
                preprompt = user.preprompt


            response = await generate_response(conversation_history, preprompt)

        await client.send_message(event.chat_id, response)
    except Exception as e:
        await client.send_message(LOGGING_CHAT_ID, f"Error: {e}")

async def main():
    # Initialize the Telegram client
    # Connect and sign in using the phone number

    await client.start()

    client.add_event_handler(on_new_message, events.NewMessage)

    await client.run_until_disconnected()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())