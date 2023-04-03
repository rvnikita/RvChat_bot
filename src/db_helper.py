from sqlalchemy import Column, String, DateTime, Integer, create_engine, Boolean, ForeignKey
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy.orm import Session, relationship
from contextlib import contextmanager
import datetime
import os
import psycopg2

class Base(DeclarativeBase):
    __prefix__ = 'rvchatbot_'

    @declared_attr
    def __tablename__(cls):
        return cls.__prefix__ + cls.__name__.lower()


class User(Base):

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    status = Column(String)
    last_message_datetime = Column(DateTime)
    memory = Column(String)
    requests_counter = Column(Integer, default=0)

class MessageQueue(Base):
    id = Column(Integer, primary_key=True)
    message = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_test = Column(Boolean, default=False)

    user_messages = relationship("UserMessage", back_populates="message_queue")

class UserMessage(Base):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('rvchatbot_user.id'))
    message_queue_id = Column(Integer, ForeignKey('rvchatbot_messagequeue.id'))

    sent_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="user_messages")
    message_queue = relationship("MessageQueue", back_populates="user_messages")

User.user_messages = relationship("UserMessage", order_by=UserMessage.id, back_populates="user")


@contextmanager
def get_session():
    engine = create_engine(
        f"postgresql://{os.environ['ENV_DB_USER']}:{os.environ['ENV_DB_PASSWORD']}@{os.environ['ENV_DB_HOST']}:{os.environ['ENV_DB_PORT']}/{os.environ['ENV_DB_NAME']}")

    session = Session(engine)

    try:
        yield session
    except:
        session.rollback()
        raise
    else:
        session.commit()

    return session

session = get_session()

