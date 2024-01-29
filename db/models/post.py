from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func
from ..base import Base

class Post(Base):
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True, index=True)
    assistant_id = Column(String, index=True)
    language_code = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # New column to store the count of messages sent to different users
    message_count = Column(Integer, default=0)

    # New column for text content, limited to 3000 symbols
    text_content = Column(Text, nullable=True)

    # New column for storing image URL
    image_url = Column(String, nullable=True)

    # New column for title
    title = Column(String, nullable=True)
