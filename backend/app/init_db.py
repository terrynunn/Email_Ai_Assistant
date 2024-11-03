from sqlalchemy_utils import database_exists, create_database
from .database import engine
from . import models

def init_database():
    # Create database if it doesn't exist
    if not database_exists(engine.url):
        create_database(engine.url)
    
    # Create all tables
    models.Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_database()
    print("Database initialized successfully!") 