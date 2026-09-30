"""
src/core/database.py
Persistent storage engine for CAD/GD&T inspections and historical telemetry.
"""
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./metrology_history.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class InspectionRecord(Base):
    __tablename__ = "inspection_records"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    part_number = Column(String(64), index=True)
    serial_number = Column(String(64), index=True)
    total_characteristics = Column(Integer)
    status = Column(String(16))
    cp = Column(Float)
    cpk = Column(Float)
    operator = Column(String(64))
    characteristics_json = Column(Text)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
