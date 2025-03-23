from pydantic import BaseModel, ConfigDict

from src.desktop_client.test_configuration.scenario_steps import ScenarioStep


class DbTestConf(BaseModel):
    db_image: str
    scenario_steps: list[ScenarioStep]

    model_config = ConfigDict(arbitrary_types_allowed=True)
