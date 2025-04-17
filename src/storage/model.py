import datetime
import json
from typing import Any

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import declarative_base

from src.core.scenario_steps import ScenarioStep, deserialize_step

Base = declarative_base()


class TestResults(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(Text, nullable=False)
    db_image = Column(Text, nullable=False)
    operation = Column(Text, nullable=False)
    num_records = Column(Integer, nullable=False)
    step_description = Column(Text, nullable=True)
    execution_time = Column(Float, nullable=True)
    memory_used = Column(Float, nullable=True)
    cpu_percent = Column(Float, nullable=True)


class DockerImage(Base):
    __tablename__ = "docker_image"

    id = Column(Integer, primary_key=True, autoincrement=True)
    image_name = Column(String, unique=False, nullable=False)
    config_name = Column(String, unique=True, nullable=False)
    config = Column(Text, nullable=True)
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.UTC),
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.UTC),
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.created_at = datetime.datetime.now(datetime.UTC)
        self.updated_at = datetime.datetime.now(datetime.UTC)

    def get_config_as_json(self):
        return json.loads(self.config)


class AiConfig(Base):
    __tablename__ = "ai_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)

    config = Column(Text, nullable=True)

    def get_config_as_dict(self) -> dict[str, Any]:
        if not self.config:
            return {}
        return json.loads(self.config)


class Scenario(Base):
    __tablename__ = "scenario"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    timestamp_created = Column(DateTime, default=datetime.datetime.now(datetime.UTC))
    timestamp_updated = Column(DateTime, default=datetime.datetime.now(datetime.UTC))

    steps = Column(Text, nullable=True)

    def set_steps(self, steps: list[ScenarioStep]) -> None:
        steps_data = [json.loads(step.json()) for step in steps]
        self.steps = json.dumps(steps_data)

    def get_steps(self) -> list[ScenarioStep]:
        if not self.steps:
            return []
        return [deserialize_step(step) for step in json.loads(self.steps)]
