from sqlalchemy import Column, DateTime, Integer, String, DECIMAL
from sqlalchemy.sql import func
from lib.openai.tokenizer import Tokenizer
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
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    balance = Column(DECIMAL(precision=10, scale=5), default=Tokenizer.START_BALANCE)

# Example of update balance

# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from db.models.conversation import Conversation  # Replace 'your_model_file' with the actual file name

# # SQLite database connection string
# DATABASE_URL = "sqlite:///db/aihelper.db"  # Replace with the path to your SQLite database file

# # Set up the database engine and session
# engine = create_engine(DATABASE_URL)
# Session = sessionmaker(bind=engine)
# session = Session()

# # Assuming you know the ID of the Conversation
# conversation_id = 10  # Replace with the actual conversation ID

# # Query the Conversation
# conversation = session.query(Conversation).filter(Conversation.id == conversation_id).first()

# # session.delete(conversation)

# # Update the balance
# # conversation.balance = 0.0

# conversation.language_code = 'ua'

# # Commit the changes to the database
# session.commit()
# session.close()
