"""The sqlite model for a file."""
from archivebot.db import base
from sqlalchemy import Column, String, Integer, Boolean


class File(base):
    """The sqlite model for a file."""

    __tablename__ = 'file'

    file_id = Column(String(), primary_key=True)
    chat_id = Column(Integer())
    message_id = Column(Integer())
    user_id = Column(Integer())
    file_name = Column(String())
    file_type = Column(String())
    success = Column(Boolean(), nullable=False, default=False)

    def __init__(self, file_id, chat_id, message_id, user_id, name, file_type):
        """Create a new file."""
        self.file_id = file_id
        self.chat_id = chat_id
        self.message_id = message_id
        self.user_id = user_id
        self.file_name = name
        self.file_type = file_type
