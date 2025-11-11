from sqlmodel import SQLModel, create_engine, Session
from typing import Generator


sqlite_file_name = "mergington.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# For SQLite we must disable same-thread check for SQLModel/SQLAlchemy when using in FastAPI dev server
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})


def init_db() -> None:
    """Create database tables."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def seed_data() -> None:
    """Seed sample activities if the DB is empty."""
    from sqlmodel import select

    # import Activity model locally to avoid import cycles
    from .models import Activity

    with Session(engine) as session:
        has = session.exec(select(Activity)).first()
        if has:
            return

        samples = [
            {
                "name": "Chess Club",
                "description": "Learn strategies and compete in chess tournaments",
                "schedule": "Fridays, 3:30 PM - 5:00 PM",
                "max_participants": 12,
            },
            {
                "name": "Programming Class",
                "description": "Learn programming fundamentals and build software projects",
                "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
                "max_participants": 20,
            },
            {
                "name": "Gym Class",
                "description": "Physical education and sports activities",
                "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
                "max_participants": 30,
            },
        ]

        for s in samples:
            a = Activity(**s)
            session.add(a)

        session.commit()
