from typing import Optional
from datetime import datetime, UTC

from sqlmodel import Field, SQLModel


class QuizPrediction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_name: str = Field(index=True)
    event_category: str  # e.g., "Lancer Homme", "Points du Jour"
    prediction_type: str  # e.g., "Place 1", "Place 2", "Total Points"
    predicted_value: str  # Athlete's name or points value
    submission_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), nullable=False
    )


# Code to create the database engine and tables
from sqlalchemy import create_engine
from dotenv import find_dotenv, load_dotenv
import os

# Load the stored environment variables
load_dotenv(find_dotenv())

# Get the values
username = os.getenv("DATABASE_USERNAME")
password = os.getenv("DATABASE_PASSWORD")
host = os.getenv("DATABASE_HOST")
port = os.getenv("DATABASE_PORT")
database = os.getenv("DATABASE_NAME")

# Construct the connection URL
# Add a fallback for DATABASE_URL if individual components are not set
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    if not all([username, password, host, port, database]):
        raise ValueError(
            "Database connection details not found in environment variables. Please set DATABASE_USERNAME, DATABASE_PASSWORD, DATABASE_HOST, DATABASE_PORT, and DATABASE_NAME, or provide a complete DATABASE_URL."
        )
    DATABASE_URL = (
        f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"
    )

# Create the database engine
engine = create_engine(DATABASE_URL)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
