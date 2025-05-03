from pydantic import BaseModel, ConfigDict, Field
from src.app.core.scenario_steps import ScenarioStep
from src.app.storage.model import DockerImage


class DockerHostConfig(BaseModel):
    """Конфигурация для подключения к Docker хосту."""

    base_url: str | None = Field(
        default=None,
        description="URL для подключения к Docker daemon (например, 'tcp://192.168.1.100:2376')",
    )
    tls_ca_cert: str | None = Field(
        default=None,
        description="Путь к CA сертификату для TLS",
    )
    tls_client_cert: str | None = Field(
        default=None,
        description="Путь к клиентскому сертификату для TLS",
    )
    tls_client_key: str | None = Field(
        default=None,
        description="Путь к клиентскому ключу для TLS",
    )
    tls_verify: bool = Field(default=True, description="Проверять ли TLS сертификаты")
    version: str | None = Field(default=None, description="Версия API Docker")
    timeout: int | None = Field(
        default=None,
        description="Таймаут для операций с Docker в секундах",
    )


class TestSystemConfig(BaseModel):
    use_existing: bool = False
    stop_after: bool = False
    remove_after: bool = False


class DbTestConf(BaseModel):
    db_config: DockerImage
    scenario_steps: list[ScenarioStep]
    docker_host: DockerHostConfig | None = Field(
        default=None,
        description="Конфигурация для подключения к Docker хосту. Если None, используется локальный хост.",
    )
    test_system_config: TestSystemConfig

    model_config = ConfigDict(arbitrary_types_allowed=True)
