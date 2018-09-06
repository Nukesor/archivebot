"""The sqlite model for a subscriber."""
from archivebot.db import base

from sqlalchemy import Column, String, Integer, Boolean


class Subscriber(base):
    """The sqlite model for a subscriber."""

    __tablename__ = 'subscriber'

    chat_id = Column(Integer(), primary_key=True)
    chat_type = Column(String, primary_key=True)
    channel_name = Column(String(), nullable=False)
    accepted_media = Column(String(), nullable=False, default='')
    allow_duplicates = Column(Boolean(), nullable=False, default=True)
    active = Column(Boolean(), nullable=False, default=False)
    verbose = Column(Boolean(), nullable=False, default=False)
    sort_by_user = Column(Boolean(), nullable=False, default=True)

    def __init__(self, chat_id, chat_type, channel_name=None, accepted_media='document'):
        """Create a new subscriber."""
        self.chat_id = chat_id
        self.chat_type = chat_type
        self.channel_name = channel_name or chat_id
        self.accepted_media = accepted_media

    @staticmethod
    def get_or_create(session, chat_id, chat_type, channel_name=None):
        """Get or create a new subscriber."""
        subscriber = session.query(Subscriber).get((chat_id, chat_type))
        if not subscriber:
            subscriber = Subscriber(chat_id, chat_type, channel_name=channel_name)
            session.add(subscriber)
            session.commit()

        return subscriber
