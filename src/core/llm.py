from langchain.chains.llm import LLMChain
from langchain_community.chat_models.yandex import ChatYandexGPT
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field, RootModel, validator
from src.config.config import settings
from src.schemas.enums import DataType

llm = ChatYandexGPT(
    api_key=settings.YANDEX_API_KEY,
    folder_id=settings.YANDEX_FOLDER_ID,
    model_name="yandexgpt"
)


class CreateTableStep(BaseModel):
    table_name: str = Field(description="Название таблицы")
    columns: dict[str, DataType] = Field(description="Словарь колонок и их типов данных")


# Определяем корневую модель для списка таблиц
class TablesList(RootModel[list[CreateTableStep]]):
    pass


def get_tables_list(sql_query: str) -> list[CreateTableStep]:
    parser = PydanticOutputParser(pydantic_object=TablesList)

    format_instructions = parser.get_format_instructions()

    template = (
        "Анализируй следующий SQL-запрос и извлеки из него информацию о всех таблицах, "
        "которые упоминаются в запросе, а также все колонки каждой таблицы. Включи не только колонки, "
        "указанные в списке SELECT, но и те, которые используются для объединения (например, в операторе USING). \n\n"
        "Например, если запрос содержит 'SELECT a.*, b.name FROM a INNER JOIN b USING(id) WHERE a.age > 15', \n"
        "то результатом должно быть описание двух таблиц:\n"
        "- Таблица 'a' с колонками, например, 'id' и 'age'.\n"
        "- Таблица 'b' с колонками 'id' и 'name'.\n\n"
        "Если тип данных для колонки не очевиден, определи его по контексту (например, 'age' → int, 'name' → str). \n\n"
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
        return llm_chain.invoke(sql_query)
    except Exception as e:
        print("Ошибка:", e)


if __name__ == '__main__':
    sql_query = "SELECT a.*, b.name FROM a INNER JOIN b USING(id) LEFT join c on b.mpn = c.mfr WHERE a.age > 15"

    tables = get_tables_list(sql_query)
    print(tables)
