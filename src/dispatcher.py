import os
from telethon import TelegramClient, events, types
from telethon.sessions import StringSession
import openai
import json

# Get API credentials from environment variables
API_ID = os.environ['API_ID']
API_HASH = os.environ['API_HASH']
PHONE_NUMBER = os.environ['PHONE_NUMBER']
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
TELEGRAM_SESSION_STRING = os.environ['TELEGRAM_SESSION_STRING']

openai.api_key = OPENAI_API_KEY
client = TelegramClient(StringSession(TELEGRAM_SESSION_STRING), API_ID, API_HASH)

async def generate_response(conversation_history):
    me = await client.get_me()

    prompt = []

    #loop through the conversation history
    for message in reversed(conversation_history):
        if message.sender == me: #from bot
            prompt.append({"role": "assistant", "content": message.text})
        else:
            prompt.append({"role": "user", "content": message.text})

    # temporary log to admin
    await client.send_message(88834504, json.dumps(prompt, indent=4))

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
        if msg.text == '/clear':
            break
        if total_tokens + len(msg.text) <= max_tokens:
            messages.append(msg)
            total_tokens += len(msg.text)
            min_id = msg.id
        else:
            break

    return reversed(messages[::-1])

async def on_new_message(event):
    try:
        if event.chat_id != 88834504:
            # For now debug only on my account
            return
        elif event.text == '/clear':
            await client.send_message(event.chat_id, "Clearing conversation history")
            return

        async with client.action(event.chat_id, 'typing'):
            conversation_history = await get_last_x_messages(client, event.chat_id, 500)
            response = await generate_response(conversation_history)

        await client.send_message(event.chat_id, response)
    except Exception as e:
        await client.send_message(event.chat_id, f"Error: {e}")

async def main():
    # Initialize the Telegram client
    # Connect and sign in using the phone number

    await client.start()

    client.add_event_handler(on_new_message, events.NewMessage)

    await client.run_until_disconnected()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())