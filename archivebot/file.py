"""The sqlite model for a file."""
from archivebot.db import base
from sqlalchemy import Column, String, Integer, Boolean


class File(base):
    """The sqlite model for a file."""

    __tablename__ = 'file'

    message_id = Column(Integer(), primary_key=True)
    chat_id = Column(Integer())
    chat_type = Column(String())
    user_id = Column(Integer())
    file_id = Column(String())
    file_type = Column(String())
    file_name = Column(String())
    file_path = Column(String())
    success = Column(Boolean(), nullable=False, default=False)

    def __init__(self, file_id, chat_id, chat_type,
                 user_id, message_id,
                 file_type, file_name, file_path):
        """Create a new file."""
        self.file_id = file_id
        self.chat_id = chat_id
        self.user_id = user_id
        self.message_id = message_id
        self.file_type = file_type
        self.file_name = file_name
        self.file_path = file_path

    def exists(session, chat_id, file_id):
        """Check if we already have this file."""
        return session.query(File) \
            .filter(File.chat_id == chat_id) \
            .filter(File.file_id == file_id) \
            .all()
