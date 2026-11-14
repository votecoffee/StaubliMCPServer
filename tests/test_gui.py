import os
import pytest
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication
from staubli_workbench.gui import MainWindow


def test_worker_populates_result_and_releases_controls():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    loop = QEventLoop()
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)
    window.run_operation()
    window.worker.finished.connect(loop.quit)
    timer.start(5000)
    loop.exec()
    app.processEvents()
    assert window.worker is None
    assert window.last_result["ok"] and window.tree.topLevelItemCount() > 0
    assert window.run_button.isEnabled() and window.operations.isEnabled()
    window.close()
