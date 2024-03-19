from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# Assuming you have defined your database URL
DATABASE_URL = "postgresql://root:root@localhost/dat_backend"

# Create the engine
engine = create_engine(DATABASE_URL)

# Create a sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()