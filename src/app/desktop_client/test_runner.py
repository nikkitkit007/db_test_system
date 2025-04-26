from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from src.app.config.log import get_logger
from src.app.core.docker_test import run_test
from src.app.core.scenario_steps import ScenarioStep
from src.app.schemas.schema import DbTestConf, DockerHostConfig, TestSystemConfig
from src.app.storage.model import DockerImage

logger = get_logger(__name__)


class DockerTestRunner(QObject):
    log = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(
        self,
        db_config: DockerImage,
        scenario_steps: list[ScenarioStep],
        test_system_config: TestSystemConfig,
        docker_host: DockerHostConfig | None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.db_config = db_config
        self.scenario_steps = scenario_steps
        self.test_system_config = test_system_config
        self.docker_host = docker_host

    @pyqtSlot()
    def run(self) -> None:
        self.log.emit("✨ Запускаем тест...")
        try:

            run_test(
                DbTestConf(
                    db_config=self.db_config,
                    scenario_steps=self.scenario_steps,
                    test_system_config=self.test_system_config,
                    docker_host=self.docker_host,
                ),
                log_fn=self.log.emit,
            )
            self.log.emit("🟢 Тест завершён.")
        except Exception as e:
            logger.exception("Ошибка в DockerTestWorker: %s", e)
        finally:
            self.finished.emit()
