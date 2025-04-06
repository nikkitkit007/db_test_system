from typing import Any

from langchain_community.chat_models.yandex import ChatYandexGPT
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field, RootModel

import src.core.scenario_steps as steps
from src.config.config import settings
from src.config.log import get_logger
from src.schemas.enums import DataType, data_type_list  # noqa
from src.storage.model import AiConfig

logger = get_logger(__name__)


class CreateTableStep(BaseModel):
    table_name: str = Field(description="Название таблицы")
    columns: dict[str, str] = Field(description="Словарь колонок и их типов данных")


# Определяем корневую модель для списка таблиц
class TablesList(RootModel[list[CreateTableStep]]):
    pass


def get_tables_list(sql_query: str, llm_config: dict[str, Any]) -> list[steps.CreateTableStep]:
    llm = ChatYandexGPT(
        api_key=llm_config['api_key'],
        folder_id=llm_config['folder_id'],
        model_name=llm_config.get("model_name") or "yandexgpt",
    )
    # llm = ChatYandexGPT(
    #     api_key=settings.YANDEX_API_KEY,
    #     folder_id=settings.YANDEX_FOLDER_ID,
    #     model_name="yandexgpt",
    # )

    parser = PydanticOutputParser(pydantic_object=TablesList)

    format_instructions = parser.get_format_instructions()

    template = (
        "Проанализируй следующий SQL-запрос и извлеки информацию обо всех таблицах и их столбцах. "
        "Обрати внимание на следующие моменты:\n"
        "- Таблицы могут быть указаны с алиасами. Если алиас используется, попробуй вернуть исходное имя таблицы или укажи алиас.\n"
        "- Если используется символ '*', укажи, что выбираются все колонки, либо перечисли возможные колонки, если это возможно определить по контексту.\n"
        "- Включи в результат все колонки, указанные в списке SELECT, а также те, которые применяются в условиях объединения (JOIN, ON, USING) и в других частях запроса.\n"
        f"- Если тип данных для колонки неочевиден, выбери его из набора: {data_type_list}. Например, 'age' → int, 'name' → str.\n\n"
        "Пример:\n"
        "Если запрос: 'SELECT a.*, b.name FROM a INNER JOIN b USING(id) WHERE a.age > 15', то нужно вернуть:\n"
        "- Таблица 'a' с колонками, например, 'id' и 'age'.\n"
        "- Таблица 'b' с колонками 'id' и 'name'.\n\n"
        "Верни ответ **только** в виде валидного JSON, соответствующего следующему формату:\n"
        "{format_instructions}\n\n"
        "SQL-запрос: {query}"
    )

    prompt_template = PromptTemplate(
        template=template,
        input_variables=["query"],
        partial_variables={"format_instructions": format_instructions},
    )

    llm_chain = prompt_template | llm | parser

    try:
        create_steps: list[CreateTableStep] = llm_chain.invoke(sql_query).root or []
        return [
            steps.CreateTableStep(table_name=step.table_name, columns=step.columns)
            for step in create_steps
        ]

    except Exception as e:
        logger.exception("Ошибка:", e)


if __name__ == "__main__":
    # test_sql_query = "SELECT a.*, b.name FROM a INNER JOIN b USING(id) LEFT join c on b.mpn = c.mfr WHERE a.age > 15"
    test_sql_query = "select a, b from c"
    tables = get_tables_list(test_sql_query)
