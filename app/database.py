from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# SQLite URL (local)
SQLALCHEMY_DATABASE_URL = "sqlite:///./habits.db"

# Engine (basically a db connection)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# SessionLocal is an instance used to talk to the DB
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

# Base is the class for models to inherit from
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()