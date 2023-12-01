from sqlalchemy import Column, DateTime, Integer, String, Float
from sqlalchemy.sql import func
from ..base import Base

class Conversation(Base):
    __tablename__ = 'conversations'

    id = Column(Integer, primary_key=True, index=True)
    assistant_id = Column(String, index=True)
    thread_id = Column(String, index=True)
    user_id = Column(Integer, index=True)
    username = Column(String, index=True)
    language_code = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    balance = Column(Float(precision=5), default=1.0)
