from sqlalchemy import Column, String, DateTime, Integer, create_engine
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy.orm import Session
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


#connect to postgresql
engine = create_engine(f"postgresql://{os.environ['ENV_DB_USER']}:{os.environ['ENV_DB_PASSWORD']}@{os.environ['ENV_DB_HOST']}:{os.environ['ENV_DB_PORT']}/{os.environ['ENV_DB_NAME']}")
session = Session(engine)