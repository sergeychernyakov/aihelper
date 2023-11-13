# Import the SessionLocal instance and engine from your db.engine file
from db.engine import SessionLocal, engine
from db.models.user import User
from db.base import Base

# Ensure all tables are created
Base.metadata.create_all(bind=engine)

session = SessionLocal()

# # Create a new user instance
# new_user = User(name='Jane Doe', age=28)

# # Add and commit the new user
# session.add(new_user)
# session.commit()

# Verify insertion
user = session.query(User).filter_by(name='Jane Doe').first()
print(f'User retrieved from db: {user.name}, age: {user.age}')

# Close the session
session.close()
