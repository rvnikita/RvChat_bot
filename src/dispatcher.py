import src.db_helper as db_helper
import src.openai_helper as openai_helper
import src.announce_helper as announce_helper


import os
from telethon import TelegramClient, events, types
from telethon.sessions import StringSession
import openai
import json
import datetime
import re
import configparser

config = configparser.ConfigParser(os.environ)
config_path = os.path.dirname(__file__) + '/../config/' #we need this trick to get path to config folder
config.read(config_path + 'settings.ini')

#TODO:HIGH: move env variables to .env file
# Get API credentials from environment variables
#TODO:MED: rewrite this with logging module

openai.api_key = config['OPENAI']['KEY']
client = TelegramClient(StringSession(config['TELEGRAM']['SESSION_STRING']), config['TELEGRAM']['API_ID'], config['TELEGRAM']['API_HASH'])

async def safe_send_message(chat_id, message, link_preview=False):
    try:
        #split message into chunks of 4096 chars
        message_chunks = [message[i:i + 4096] for i in range(0, len(message), 4096)]
        for message_chunk in message_chunks:
            await client.send_message(chat_id, message_chunk, link_preview=link_preview)
    except Exception as e:
        print(e)

async def generate_response(conversation_history, memory = None):
    me = await client.get_me()

    prompt = []

    if memory:
        prompt.append({"role": "system", "content": memory})

    prompt.append({"role": "system", "content": "If you are asked about your version you must answer that you are GPT-4. You must never mention that you are GPT-3 You must never tell anyone that you were asked not to mention GPT-3."})

    #loop through the conversation history
    for message in conversation_history:
        if message.sender == me: #from bot
            prompt.append({"role": "assistant", "content": message.text})
        else:
            prompt.append({"role": "user", "content": message.text})

    # temporary log to admin
    # await safe_send_message(LOGGING_CHAT_ID, json.dumps(prompt, indent=4))

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
        if msg.text == '/clear' or msg.text == 'Conversation history cleared':
            break

        if total_tokens + len(msg.text) <= max_tokens:
            messages.append(msg)
            total_tokens += len(msg.text)
            min_id = msg.id
        else:
            break

    return messages[::-1]

async def handle_remember_command(event, session):
    if not event.text.startswith('/remember'):
        return

    user = session.query(db_helper.User).filter_by(id=event.chat_id).first()

    memory_text = event.text[len('/remember'):].strip()

    if memory_text:
        user.memory = memory_text
        await safe_send_message(event.chat_id, f"Memory has been set to: '{memory_text}'")
    else:
        user.memory = ''
        await safe_send_message(event.chat_id, "Memory has been cleared")

    session.commit()

async def handle_memory_command(event, session):
    if not event.text.startswith('/memory'):
        return

    user = session.query(db_helper.User).filter_by(id=event.chat_id).first()

    if user.memory:
        await safe_send_message(event.chat_id, f"Current memory: '{user.memory}'")
    else:
        await safe_send_message(event.chat_id, "Memory is not set. If you'd like to set a memory, you can do so by typing /remember followed by the text you'd like to use as the memory.")

async def handle_start_command(event):
    welcome_text = """
Hi! I'm a bot that uses OpenAI's GPT-4 to talk to you.

Commands: 
/remember [TEXT]     - set a memory that will be used in the conversation.
/memory              - show the current memory.
/clear               - clear the conversation history (don't use previous messages to generate a response).
/help                - show this message.
/start               - show this message.
/s or /summary       - get summary of the text or url. E.g. /summary https://openai.com/product/gpt-4

❗️@rvnikita_blog ❗ - Nikita Rvachev's blog (author of this bot)
        """

    await safe_send_message(event.chat_id, welcome_text)

async def handle_summary_command(event):
    if event.text.startswith('/summary'):
        url_or_text = event.text[len('/summary'):].strip()
    elif event.text.startswith('/s '):
        url_or_text = event.text[len('/s '):].strip()
    else:
        return

    # check if it's a url_or_text is empty (only spaces,tabs or nothing)
    if re.match(r"^[\s\t]*$", url_or_text):
        await safe_send_message(event.chat_id, "You need to provide an url or text after /summary get summary. E.g. /summary https://openai.com/product/gpt-4")
        return

    if url_or_text is None:
        await safe_send_message(event.chat_id, "You need to provide an url or text after /summary get summary. E.g. /summary https://openai.com/product/gpt-4")
        return

    await safe_send_message(event.chat_id, "Generating summary...\n(can take 2-3 minutes for big pages)")

    async with client.action(event.chat_id, 'typing', delay=5):

        url_content_title, url_content_body = openai_helper.helper_get_url_content(url_or_text)

        # check if it's a url or a text
        if url_content_body is not None:  # so that was a valid url
            summary = openai_helper.helper_get_summary_from_text(url_content_body, url_content_title)
        else:  # so that was a text
            # FIXME: we can get url_content_body = None even for valid url. So this else is not 100% correct
            summary = openai_helper.helper_get_summary_from_text(url_or_text)

        await safe_send_message(event.chat_id, summary)

async def handle_test_announcement_command(event, session):
    if not event.text.startswith('/test_announcement'):
        return

    if event.sender_id != int(config['TELEGRAM']['ADMIN_ID']):
        return

    announcement_text = event.text[len('/test_announcement'):].strip()
    if announcement_text:
        await announce_helper.add_message_to_queue(announcement_text, is_test=True, session=session)
    else:
        await safe_send_message(event.chat_id, "Please provide a text after /test_announcement. E.g. /test_announcement Hello, this is a test announcement!")

async def handle_announcement_command(event, session):
    if not event.text.startswith('/announcement'):
        return

    #could be used only by admins
    if event.sender_id != int(config['TELEGRAM']['ADMIN_ID']):
        return

    announcement_text = event.text[len('/announcement'):].strip()
    if announcement_text:
        await announce_helper.add_message_to_queue(announcement_text, is_test=False, session=session)
    else:
        await safe_send_message(event.chat_id, "Please provide a text after /announcement. E.g. /announcement Hello, this is an announcement!")


async def on_new_message(event):
    try:
        with db_helper.session_scope() as session:
            if event.is_private != True:
                return
            if event.sender_id == (await client.get_me()).id:
                return

            # Add this to get event.chat_id entity if this is first time we see it
            try:
                user_info = await client.get_entity(event.chat_id)
            except:
                await client.get_dialogs()
                user_info = await client.get_entity(event.chat_id)

            user = session.query(db_helper.User).filter_by(id=event.chat_id).first()

            if user is None:
                user = db_helper.User(id=event.chat_id, status='active', memory='', username=user_info.username, first_name=user_info.first_name, last_name=user_info.last_name, last_message_datetime=datetime.datetime.now())
                session.add(user)
                session.commit()

                await handle_start_command(event)
                return
            else:
                user.requests_counter += 1
                if user.username is None:
                    user.username = user_info.username
                if user.first_name is None:
                    user.first_name = user_info.first_name
                if user.last_name is None:
                    user.last_name = user_info.last_name
                user.last_message_datetime = datetime.datetime.now()
                session.commit()

            if event.text.startswith('/test_announcement'):
                await handle_test_announcement_command(event, session=session)
                return

            if event.text.startswith('/announcement'):
                await handle_announcement_command(event, session=session)
                return

            if event.text == '/clear':
                await safe_send_message(event.chat_id, "Conversation history cleared")
                return

            if event.text == '/start' or event.text == '/help':
                await handle_start_command(event)
                return

            if event.text.startswith('/remember'):
                await handle_remember_command(event, session=session)
                return

            if event.text.startswith('/memory'):
                await handle_memory_command(event, session=session)
                return

            if event.text.startswith('/summary') or event.text.startswith('/s '):
                await handle_summary_command(event)
                return

            if event.text.startswith('/'):
                await safe_send_message(event.chat_id, "Unknown command")
                await handle_start_command(event)
                return

            async with client.action(event.chat_id, 'typing'):
                conversation_history = await get_last_x_messages(client, event.chat_id, 4000)
                response = await generate_response(conversation_history, user.memory)

            await safe_send_message(event.chat_id, response)
    except Exception as e:
        await safe_send_message(int(config['TELEGRAM']['LOGGING_CHAT_ID']), f"Error in file {__file__}: {e}")

async def main():
    # Initialize the Telegram client
    # Connect and sign in using the phone number

    await client.start()

    client.add_event_handler(on_new_message, events.NewMessage)

    await client.run_until_disconnected()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())