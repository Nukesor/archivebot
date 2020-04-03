"""The model for a subscriber."""
from archivebot.db import base

from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship


class Subscriber(base):
    """The model for a subscriber."""

    __tablename__ = "subscriber"

    chat_id = Column(String, primary_key=True)
    chat_type = Column(String, primary_key=True)
    chat_name = Column(String, nullable=False)
    accepted_media = Column(String, nullable=False, default="")
    allow_duplicates = Column(Boolean, nullable=False, default=True)
    active = Column(Boolean, nullable=False, default=False)
    verbose = Column(Boolean, nullable=False, default=False)
    sort_by_user = Column(Boolean(), nullable=False, default=True)

    files = relationship("File")

    def __init__(self, chat_id, chat_type, chat_name=None, accepted_media="document"):
        """Create a new subscriber."""
        self.chat_id = chat_id
        self.chat_type = chat_type
        self.chat_name = chat_name or chat_id
        self.accepted_media = accepted_media

    @staticmethod
    def get_or_create(session, chat_id, chat_type, message, chat_name=None):
        """Get or create a new subscriber."""
        # If we have a user chat, we use the combination of both member ids to compile our own
        # unique identifier for this chat, since telegram doesn't give us a unique chat id for user chats.
        if chat_type == "user":
            identifier = [str(chat_id), str(message.from_id)]
            identifier.sort()
            identifier = "_".join(identifier)

        subscriber = session.query(Subscriber).get((chat_id, chat_type))
        if not subscriber:
            subscriber = Subscriber(chat_id, chat_type, chat_name=chat_name)
            session.add(subscriber)
            session.commit()

        return subscriber
