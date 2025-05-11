from typing import Optional
from datetime import datetime, UTC

from sqlmodel import Field, SQLModel, create_engine
from dotenv import find_dotenv, load_dotenv
import os
import streamlit as st  # Import Streamlit


# --- Caching the engine ---
@st.cache_resource  # Use st.cache_resource for non-data objects like connections
def get_engine():
    load_dotenv(find_dotenv())
    username = os.getenv("DATABASE_USERNAME")
    password = os.getenv("DATABASE_PASSWORD")
    host = os.getenv("DATABASE_HOST")
    port = os.getenv("DATABASE_PORT")
    database = os.getenv("DATABASE_NAME")

    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        if not all([username, password, host, port, database]):
            raise ValueError(
                "Database connection details not found in environment variables. "
                "Please set DATABASE_USERNAME, DATABASE_PASSWORD, DATABASE_HOST, "
                "DATABASE_PORT, and DATABASE_NAME, or provide a complete DATABASE_URL."
            )
        DATABASE_URL = (
            f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"
        )

    print("Creating database engine...")  # For debugging
    return create_engine(DATABASE_URL)


engine = get_engine()


# --- Model Definition ---
class QuizPrediction(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    user_name: str = Field(index=True)
    event_category: str  # e.g., "Lancer Homme", "Points du Jour"
    prediction_type: str  # e.g., "Place 1", "Place 2", "Total Points"
    predicted_value: str  # Athlete's name or points value
    submission_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), nullable=False
    )


# --- Table Creation ---
_tables_created = False


def create_db_and_tables_once():
    global _tables_created
    if not _tables_created:
        print("Attempting to create database tables...")  # For debugging
        SQLModel.metadata.create_all(engine)
        _tables_created = True
        print("Database tables created or verified.")
    else:
        print("Database tables already managed, create_all not called again.")
