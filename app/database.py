from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Assuming you have defined your database URL
DATABASE_URL = "postgresql://root:root@db-backend/dat_backend"

# Create the engine
engine = create_engine(DATABASE_URL)

# Create a sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        print("yielding database session")
        yield db
    finally:
        print("closing db session")
        db.close()