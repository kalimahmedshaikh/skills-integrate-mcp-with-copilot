"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path

from sqlmodel import Session, select

from .db import engine, init_db, get_session, seed_data
from .models import Activity, User, Registration
from .auth import router as auth_router


app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")


# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")


# Initialize the database and seed sample data
init_db()
seed_data()

# include auth routes
app.include_router(auth_router, prefix="/auth")


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities(session: Session = Depends(get_session)):
    """Return all activities and their participant lists."""
    activities = {}
    results = session.exec(select(Activity)).all()
    for act in results:
        regs = session.exec(select(Registration).where(Registration.activity_id == act.id)).all()
        participants = [session.get(User, r.user_id).email for r in regs]
        activities[act.name] = {
            "description": act.description,
            "schedule": act.schedule,
            "max_participants": act.max_participants,
            "participants": participants,
        }
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, session: Session = Depends(get_session)):
    """Sign up a student for an activity (DB-backed)."""
    activity = session.exec(select(Activity).where(Activity.name == activity_name)).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # find or create user
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        user = User(email=email)
        session.add(user)
        session.commit()
        session.refresh(user)

    # Check already registered
    existing = session.exec(
        select(Registration).where(Registration.user_id == user.id, Registration.activity_id == activity.id)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Student is already signed up")

    regs = session.exec(select(Registration).where(Registration.activity_id == activity.id)).all()
    if len(regs) >= activity.max_participants:
        raise HTTPException(status_code=400, detail="Activity is full")

    reg = Registration(user_id=user.id, activity_id=activity.id)
    session.add(reg)
    session.commit()
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, session: Session = Depends(get_session)):
    """Unregister a student from an activity"""
    activity = session.exec(select(Activity).where(Activity.name == activity_name)).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

    reg = session.exec(
        select(Registration).where(Registration.activity_id == activity.id, Registration.user_id == user.id)
    ).first()
    if not reg:
        raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

    session.delete(reg)
    session.commit()
    return {"message": f"Unregistered {email} from {activity_name}"}
