"""Helper class to create a database engine and to get a session."""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.session import sessionmaker

from archivebot.config import config

engine = create_engine(config["database"]["sql_uri"])
base = declarative_base(bind=engine)


def get_session(connection=None):
    """Get a new db session."""
    session = scoped_session(sessionmaker(bind=engine))
    return session
