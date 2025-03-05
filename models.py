from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

class Course(Base):
    __tablename__ = 'courses'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    url = Column(String)
    tasks = relationship('Task', back_populates='course')

    def __init__(self, id, name, url):
        self.id = id
        self.name = name
        self.url = url

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    url = Column(String)
    course_id = Column(Integer, ForeignKey('courses.id'))
    course = relationship('Course', back_populates='tasks')
    submissions = relationship('Submission', back_populates='task')

    def __init__(self, id, name, url):
        self.id = id
        self.name = name
        self.url = url

class Submission(Base):
    __tablename__ = 'submissions'
    id = Column(Integer, primary_key=True)
    student_name = Column(String)
    student_email = Column(String)
    status = Column(String)
    grade = Column(String)
    date = Column(String)
    files = Column(String)
    task_id = Column(Integer, ForeignKey('tasks.id'))
    task = relationship('Task', back_populates='submissions')

    def __init__(self, student_name, student_email, status, grade, date, files):
        self.student_name = student_name
        self.student_email = student_email
        self.status = status
        self.grade = grade
        self.date = date
        self.files = files