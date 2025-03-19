from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from src.config.log import get_logger
from src.core.docker_test import run_test
from src.schemas.test_init import DbTestConf, DbTestDataConf

logger = get_logger(__name__)


class DockerTestWorker(QObject):
    finished = pyqtSignal()

    # Можно добавить сигналы для логгирования, прогресса и т.д.

    def __init__(
        self,
        db_image,
        scenario_steps,  # <-- теперь мы передаём список шагов
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.db_image = db_image
        self.scenario_steps = scenario_steps

    @pyqtSlot()
    def run(self) -> None:
        """
        Здесь мы бы вызвали нашу функцию, аналогичную run_test,
        но теперь нужно учесть scenario_steps.
        Для простоты передадим их как-то в DbTestConf, либо
        создадим новую логику, которая обрабатывает каждый шаг.
        """
        try:
            # Допустим, мы расширили DbTestConf, чтобы он принимал список шагов
            # а run_test сам знает, как их интерпретировать.
            conf = DbTestConf(
                db_image=self.db_image,
                operation="Scenario",  # просто флаг
                test_data_conf=DbTestDataConf(data_types=[], num_records=0),
                scenario_steps=self.scenario_steps,  # <-- новое поле
            )
            run_test(conf)
        except Exception as e:
            logger.exception("Ошибка в DockerTestWorker: %s", e)
        finally:
            self.finished.emit()
