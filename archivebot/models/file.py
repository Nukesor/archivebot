"""The model for a file."""
from archivebot.db import base
from sqlalchemy.orm import relationship
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    ForeignKeyConstraint,
)


class File(base):
    """The model for a file."""

    __tablename__ = 'file'
    __table_args__ = (
        ForeignKeyConstraint(
            ['subscriber_chat_id', 'subscriber_chat_type'],
            ['subscriber.chat_id', 'subscriber.chat_type'],
        ),
    )

    message_id = Column(Integer, primary_key=True)
    to_id = Column(Integer, primary_key=True)
    from_id = Column(Integer, primary_key=True)
    to_type = Column(String, nullable=False)
    file_id = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    success = Column(Boolean, nullable=False, default=False)

    subscriber = relationship("Subscriber", back_populates="files")
    subscriber_chat_id = Column(Integer)
    subscriber_chat_type = Column(String)

    def __init__(self, file_id, to_id, from_id,
                 subscriber, to_type, message_id,
                 file_type, file_name, file_path):
        """Create a new file."""
        self.file_id = file_id
        self.to_id = to_id
        self.from_id = from_id
        self.to_type = to_type
        self.message_id = message_id
        self.file_type = file_type
        self.file_name = file_name
        self.file_path = file_path

        self.subscriber = subscriber

    def exists(session, subscriber, file_id):
        """Check if we already have this file."""
        return session.query(File) \
            .filter(File.file_id == file_id) \
            .filter(File.subscriber == subscriber) \
            .one_or_none()
