"""The sqlite model for a file."""
from archivebot.db import base
from sqlalchemy import Column, String, Integer, Boolean


class File(base):
    """The sqlite model for a file."""

    __tablename__ = 'file'

    chat_id = Column(Integer(), primary_key=True)
    message_id = Column(Integer(), primary_key=True)
    user_id = Column(Integer(), primary_key=True)
    file_name = Column(String(100), primary_key=True)
    success = Column(Boolean(), nullable=False, default=False)

    def __init__(self, chat_id, message_id, user_id, name):
        """Create a new file."""
        self.chat_id = chat_id
        self.message_id = message_id
        self.user_id = user_id
        self.file_name = name
