from enum import Enum
from typing import NamedTuple
from src.core.scenario_steps import CreateTableStep
import src.core.llm.models.ygpt as ygpt_predictor
from src.storage.config_storage import config_manager


class LLM(NamedTuple):
    openAI = "OpenAI"
    ygpt = "ygpt"


possible_llm = (
    LLM.openAI,
    LLM.ygpt,
)


def get_tables_list(sql_query: str, model: str) -> list[CreateTableStep]:
    ai_config = config_manager.get_ai_config(name=model)
    if model == LLM.ygpt:
        return ygpt_predictor.get_tables_list(sql_query, ai_config.get_config_as_dict())
    elif model == LLM.openAI:
        return []
