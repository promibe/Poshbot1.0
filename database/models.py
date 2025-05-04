from sqlalchemy import Column, Integer, String, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    dob = Column(Date)
    qualification = Column(String)
    phone_number = Column(String)
    email = Column(String, unique=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow())



class CourseOrder(Base):
    __tablename__ = "course_orders"

    id = Column(Integer, primary_key=True, index=True)
    course_name = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    ordered_at = Column(DateTime, default=datetime.utcnow())
    status = Column(String, default="available")  # e.g., "available", "unavailable"

