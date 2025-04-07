import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

if os.environ.get("SQLALCHEMY_DATABASE_URI"):
    engine = create_engine(
        os.environ.get("SQLALCHEMY_DATABASE_URI"),
        pool_size=100,
        max_overflow=20,
        pool_pre_ping=True
    )
else:
    engine = create_engine(
        "sqlite:///./game.db",
        connect_args={"check_same_thread": False},
    )

Base = declarative_base()
