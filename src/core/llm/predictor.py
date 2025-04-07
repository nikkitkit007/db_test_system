from typing import NamedTuple

import src.core.llm.models.ygpt as ygpt_predictor
from src.core.scenario_steps import CreateTableStep
from src.storage.db_manager.ai_config_storage import ai_config_db_manager
from src.storage.db_manager.config_storage import scenario_db_manager


class LLM(NamedTuple):
    openAI = "OpenAI"
    ygpt = "ygpt"


possible_llm = (
    LLM.openAI,
    LLM.ygpt,
)


def get_tables_list(sql_query: str, model: str) -> list[CreateTableStep]:
    ai_config = ai_config_db_manager.get_ai_config(name=model)
    if model == LLM.ygpt:
        return ygpt_predictor.get_tables_list(sql_query, ai_config.get_config_as_dict())
    if model == LLM.openAI:
        return []
    return []
