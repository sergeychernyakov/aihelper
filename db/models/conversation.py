from sqlalchemy import Column, DateTime, Integer, String, DECIMAL
from sqlalchemy.sql import func
from lib.telegram.tokenizer import Tokenizer
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
    balance = Column(DECIMAL(precision=10, scale=5), default=Tokenizer.START_BALANCE)
