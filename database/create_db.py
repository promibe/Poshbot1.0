from database import engine
from models import Base

# Create all tables in the database
Base.metadata.create_all(bind=engine)
print('Database and table created successfully')