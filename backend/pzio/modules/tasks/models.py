from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pzio.db import Base

class WorkItem(Base):
    __tablename__ = "work_items"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, index=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    type = Column(String, nullable=False)
    priority = Column(String, nullable=False)
    story_points = Column(Integer, nullable=True)
    parent_id = Column(Integer, ForeignKey("work_items.id"), nullable=True)
    assignee_id = Column(Integer, nullable=True)
    sprint_id = Column(Integer, nullable=True)
    status = Column(String, default="ToDo", nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class TimeLog(Base):
    __tablename__ = "time_logs"

    id = Column(Integer, primary_key=True, index=True)
    work_item_id = Column(Integer, ForeignKey("work_items.id", ondelete="CASCADE"), nullable=False)
    hours_spent = Column(Float, nullable=False)
    note = Column(Text, nullable=True)
    user_id = Column(Integer, nullable=False) # Wypełniane z tokena JWT modułu Auth
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    work_item_id = Column(Integer, ForeignKey("work_items.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, nullable=False)
    action = Column(String, nullable=False) # Np. "STATUS_CHANGE"
    old_status = Column(String, nullable=True)
    new_status = Column(String, nullable=True)
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now())