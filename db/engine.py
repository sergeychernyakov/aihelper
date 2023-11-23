from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .base import Base  # Make sure this is an absolute import

DATABASE_URI = 'sqlite:///db/aihelper.db'

engine = create_engine(DATABASE_URI, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import your models after engine creation to avoid circular imports
# (rest of your model imports here)

# Optional here: Create all tables in the database (if they do not exist)
Base.metadata.create_all(bind=engine)
