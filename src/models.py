from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, nullable=False)
    name: Optional[str] = None
    hashed_password: Optional[str] = None
    role: str = Field(default="student")

    registrations: List["Registration"] = Relationship(back_populates="user")


class Activity(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, nullable=False)
    description: Optional[str] = None
    schedule: Optional[str] = None
    max_participants: int = Field(default=20)
    is_published: bool = Field(default=True)

    registrations: List["Registration"] = Relationship(back_populates="activity")


class Registration(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    activity_id: int = Field(foreign_key="activity.id")
    attended: bool = Field(default=False)

    user: Optional[User] = Relationship(back_populates="registrations")
    activity: Optional[Activity] = Relationship(back_populates="registrations")
