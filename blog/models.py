from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime,date
from zoneinfo import ZoneInfo

Base = declarative_base()

def get_ist_time():
    return datetime.now(ZoneInfo("Asia/Kolkata"))

class Blog(Base):
    __tablename__ = 'blogs'

    blog_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_date = Column(Date, default=lambda: date.today())
    title = Column(String, nullable=False)
    body = Column(String, nullable=False)
    author_name = Column(String, nullable=False)
    created_by = Column(String)
    updated_datetime = Column(DateTime, nullable=True)


class User(Base):
    __tablename__ = 'users'

    email = Column(String, primary_key=True, nullable=False)
    name = Column(String,nullable=False) 
    password = Column(String, nullable=False)


class Ratings(Base):
    __tablename__ = 'ratings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    rating = Column(Integer, nullable=False)
    email = Column(String, ForeignKey('users.email'), nullable=False)
    blog_name = Column(String, nullable=False)

