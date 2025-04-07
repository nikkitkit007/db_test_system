from src.config.config import settings
from src.config.log import get_logger
from src.storage.db_manager.db import SQLiteDB
from src.storage.model import Scenario

logger = get_logger(__name__)


class ScenarioStorage(SQLiteDB):
    def get_all_scenarios(self) -> list[Scenario]:
        with self.session_scope() as session:
            return session.query(Scenario).all()

    def get_scenario(
        self,
        scenario_id: int | None = None,
        name: str | None = None,
    ) -> Scenario:
        if scenario_id is not None:
            query_filter = Scenario.id == scenario_id
        elif name is not None:
            query_filter = Scenario.name == name
        else:
            msg = "Not filters"
            raise Exception(msg)

        with self.session_scope() as session:
            return session.query(Scenario).filter(query_filter).first()

    def add_scenario(self, scenario: Scenario) -> Scenario:
        with self.session_scope() as session:
            session.add(scenario)
            session.flush()
            return scenario

    def update_scenario(self, scenario: Scenario) -> Scenario:
        with self.session_scope() as session:
            updated_scenario = session.merge(scenario)
            session.flush()
            return updated_scenario

    def delete_scenario(self, scenario_id: int) -> None:
        with self.session_scope() as session:
            image = session.get(Scenario, scenario_id)
            if not image:
                msg = f"Образ с ID {scenario_id} не найден."
                raise ValueError(msg)
            session.delete(image)


scenario_db_manager = ScenarioStorage(settings.SQLITE_DB_URL)
