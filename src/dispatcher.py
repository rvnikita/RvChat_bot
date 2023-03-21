import os
from telethon import TelegramClient, events
import openai

# Get API credentials from environment variables
API_ID = os.environ['API_ID']
API_HASH = os.environ['API_HASH']
PHONE_NUMBER = os.environ['PHONE_NUMBER']
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

openai.api_key = OPENAI_API_KEY
client = TelegramClient('my_user_account', API_ID, API_HASH)

async def generate_response(conversation_history):
    me = await client.get_me()

    prompt = []

    #loop through the conversation history
    for message in reversed(conversation_history):
        if message.sender == me: #from bot
            prompt.append({"role": "assistant", "content": message.text})
        else:
            prompt.append({"role": "user", "content": message.text})


    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=prompt
    )

    reply_text = response.choices[0].message.content.strip()
    return reply_text

    # prompt = f"{' '.join(conversation_history)}\n\nBot:"
    # response = openai.Completion.create(
    #     engine="gpt-4",
    #     prompt=prompt,
    #     max_tokens=50,
    #     n=1,
    #     stop=None,
    #     temperature=0.5
    # )
    # reply_text = response.choices[0].text.strip()
    # return reply_text

async def get_last_x_messages(client, channel_id, limit):
    # Get the channel entity
    channel = await client.get_entity(channel_id)

    # Fetch the last `limit` messages from the channel
    messages = await client.get_messages(channel, limit=limit)

    return messages

async def on_new_message(event):
    if event.chat_id != 88834504:
        # For now debug only on my account
        return

    await event.respond('/typing')

    conversation_history = await get_last_x_messages(client, event.chat_id, 10)

    await event.respond('/typing')

    response = await generate_response(conversation_history)

    await event.reply(response)


async def main():
    # Initialize the Telegram client
    # Connect and sign in using the phone number
    await client.start(PHONE_NUMBER)

    # Register the event handler
    client.add_event_handler(on_new_message, events.NewMessage)

    # channel_id = 88834504
    # messages = await get_last_x_messages(client, channel_id, 100)
    # conversation_history = [message.text for message in messages]

    # response = await generate_response(conversation_history)

    # await client.send_message(channel_id, response)

    # Disconnect the client
    await client.run_until_disconnected()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())