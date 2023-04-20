from sqlalchemy import Column, String, DateTime, Integer, create_engine, Boolean, ForeignKey, BigInteger
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy.orm import Session, relationship
import os
import configparser
import datetime
from contextlib import contextmanager
import os
import psycopg2

config = configparser.ConfigParser(os.environ)
config_path = os.path.dirname(__file__) + '/../config/' #we need this trick to get path to config folder
config.read(config_path + 'settings.ini')

#TODO:HIGH: разобраться с расхождениями alembic в таблицах rvchatbot_messagequeue и rvchatbot_usermessage

class Base(DeclarativeBase):
    __prefix__ = 'rvchatbot_'

    @declared_attr
    def __tablename__(cls):
        return cls.__prefix__ + cls.__name__.lower()


class User(Base):

    id = Column(BigInteger, primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    status = Column(String)
    last_message_datetime = Column(DateTime(timezone=True))
    memory = Column(String)
    openai_model = Column(String, nullable=True)


class UserDailyActivity(Base):
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey(User.__table__.c.id))
    date = Column(DateTime, default=datetime.date.today)

    command_name = Column(String)
    usage_count = Column(Integer, default=0)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)

    user = relationship("User", back_populates="daily_activities")

User.daily_activities = relationship("UserDailyActivity", order_by=UserDailyActivity.date, back_populates="user")


class MessageQueue(Base):
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    message = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    is_test = Column(Boolean, default=False)

    user_messages = relationship("UserMessage", back_populates="message_queue")

class UserMessage(Base):
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey(User.__table__.c.id))
    message_queue_id = Column(BigInteger, ForeignKey(MessageQueue.__table__.c.id))

    sent_at = Column(DateTime, nullable=True)
    status = Column(String, default='queued', nullable=False)

    user = relationship("User", back_populates="user_messages")
    message_queue = relationship("MessageQueue", back_populates="user_messages")

User.user_messages = relationship("UserMessage", order_by=UserMessage.id, back_populates="user")




#connect to postgresql
session = None

@contextmanager
def session_scope():
    db_engine = create_engine(f"postgresql://{config['DB']['USER']}:{config['DB']['PASSWORD']}@{config['DB']['HOST']}:{config['DB']['PORT']}/{config['DB']['NAME']}")
    session = Session(db_engine)

    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
        db_engine.dispose()