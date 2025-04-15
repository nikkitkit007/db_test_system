from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from src.config.log import get_logger
from src.core.docker_test import run_test
from src.core.scenario_steps import ScenarioStep
from src.schemas.test_init import DbTestConf

logger = get_logger(__name__)


class DockerTestRunner(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(
        self,
        db_image: str,
        scenario_steps: list[ScenarioStep],
        host: str = None,
        port: int = None,
        use_existing: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.db_image = db_image
        self.scenario_steps = scenario_steps
        self.host = host
        self.port = port
        self.use_existing = use_existing

    @pyqtSlot()
    def run(self) -> None:
        try:
            run_test(
                DbTestConf(
                    db_image=self.db_image,
                    scenario_steps=self.scenario_steps,
                ),
            )
        except Exception as e:
            logger.exception("Ошибка в DockerTestWorker: %s", e)
        finally:
            self.finished.emit()
