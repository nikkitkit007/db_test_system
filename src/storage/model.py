
from sqlalchemy import Column, Float, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class TestResults(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(Text, nullable=False)
    db_image = Column(Text, nullable=False)
    operation = Column(Text, nullable=False)
    num_records = Column(Integer, nullable=False)
    data_types = Column(Text, nullable=False)
    execution_time = Column(Float, nullable=True)
    memory_used = Column(Float, nullable=True)


class DockerImage(Base):
    __tablename__ = "docker_image"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
