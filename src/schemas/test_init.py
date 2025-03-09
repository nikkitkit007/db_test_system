from pydantic import BaseModel

from src.schemas.enums import DataType


class DbTestDataConf(BaseModel):
    num_records: int
    data_types: list[DataType]


class DbTestConf(BaseModel):
    db_image: str
    operation: str
    test_data_conf: DbTestDataConf
