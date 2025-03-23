from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from src.config.log import get_logger
from src.core.docker_test import run_test
from src.desktop_client.test_configuration.scenario_steps import ScenarioStep
from src.schemas.test_init import DbTestConf

logger = get_logger(__name__)


class DockerTestRunner(QObject):
    finished = pyqtSignal()

    def __init__(
        self,
        db_image,
        scenario_steps: list[ScenarioStep],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.db_image = db_image
        self.scenario_steps = scenario_steps

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
