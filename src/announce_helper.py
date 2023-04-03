from src.db_helper import session, User, MessageQueue, UserMessage

import asyncio
import os
import configparser
import datetime


config = configparser.ConfigParser(os.environ)
config_path = os.path.dirname(__file__) + '/../config/' #we need this trick to get path to config folder
config.read(config_path + 'settings.ini')

async def add_message_to_queue(message, is_test=False):
    new_message = MessageQueue(message=message, is_test=is_test)
    session.add(new_message)
    session.commit()

    users = session.query(User).all()
    for user in users:
        if not is_test or user.id == int(config['TELEGRAM']['ADMIN_ID']):
            user_message = UserMessage(user_id=user.id, message_queue_id=new_message.id, sent_at=None)
            session.add(user_message)
    session.commit()

async def process_message_queue(client):
    messages = session.query(MessageQueue).join(UserMessage).filter(UserMessage.sent_at.is_(None)).all()

    for message in messages:
        unsent_user_messages = session.query(UserMessage).filter(UserMessage.message_queue_id == message.id, UserMessage.sent_at.is_(None)).all()
        for user_message in unsent_user_messages:
            user = session.query(User).filter(User.id == user_message.user_id).first()

            # Send the message
            await client.send_message(user.id, message.message)
            user_message.sent_at = datetime.datetime.utcnow()
            session.commit()

            # You can add a delay here if needed to avoid being flagged as spam
            await asyncio.sleep(1)