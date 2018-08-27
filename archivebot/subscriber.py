"""The sqlite model for a subscriber."""
from archivebot.db import base

from sqlalchemy import Column, String, Integer, Boolean


class Subscriber(base):
    """The sqlite model for a subscriber."""

    __tablename__ = 'subscriber'

    chat_id = Column(Integer(), primary_key=True)
    group_name = Column(String())
    active = Column(Boolean(), nullable=False, default=False)

    def __init__(self, chat_id, group_name):
        """Create a new subscriber."""
        self.chat_id = chat_id
        self.group_name = group_name

    @staticmethod
    def get_or_create(session, chat_id, group_name):
        """Get or create a new subscriber."""
        subscriber = session.query(Subscriber).get(chat_id)
        if not subscriber:
            subscriber = Subscriber(chat_id, group_name)
            session.add(subscriber)
            session.commit()
            subscriber = session.query(Subscriber).get(chat_id)

        return subscriber
