"""Optional Qt desktop, sharing the CLI service catalog and dispatcher."""
from __future__ import annotations
import inspect
import json
from pathlib import Path
import sys
from PySide6.QtCore import QSettings, QThread, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QListWidget, QSplitter, QFormLayout, QLineEdit, QPushButton, QFileDialog,
    QPlainTextEdit, QTreeWidget, QTreeWidgetItem, QTabWidget, QComboBox, QCheckBox,
    QSpinBox, QDoubleSpinBox, QMessageBox, QScrollArea)
from . import __version__
from .registry import OPERATIONS, execute


class Worker(QThread):
    result = Signal(dict)

    def __init__(self, name, arguments, parent=None):
        super().__init__(parent)
        self.name, self.arguments = name, arguments

    def run(self):
        self.result.emit(execute(self.name, self.arguments))


class MainWindow(QMainWindow):
    def __init__(self, settings=None):
        super().__init__()
        self.setWindowTitle(f"Stäubli Workbench {__version__}")
        self.resize(1180, 780)
        self.settings = settings if settings is not None else QSettings("StaubliWorkbench", "Desktop")
        self.worker, self.last_result = None, None
        central = QWidget()
        layout = QVBoxLayout(central)
        title = QLabel("Stäubli Workbench")
        title.setStyleSheet("font-size: 25px; font-weight: 600; padding: 12px 4px")
        layout.addWidget(title)
        layout.addWidget(QLabel("Saved projects · VAL3 source · SRS installation · Local simulator"))
        self.splitter = QSplitter()
        self.operations = QListWidget()
        for op in OPERATIONS:
            self.operations.addItem(op.name)
        self.operations.setMinimumWidth(210)
        self.splitter.addWidget(self.operations)
        right = QWidget()
        panel = QVBoxLayout(right)
        self.description = QLabel()
        self.description.setWordWrap(True)
        panel.addWidget(self.description)
        self.form_widget = QWidget()
        self.form = QFormLayout(self.form_widget)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.form_widget)
        scroll.setMinimumHeight(190)
        panel.addWidget(scroll)
        buttons = QHBoxLayout()
        self.run_button = QPushButton("Run operation")
        self.run_button.clicked.connect(self.run_operation)
        buttons.addWidget(self.run_button)
        self.save_button = QPushButton("Save result…")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_result)
        buttons.addWidget(self.save_button)
        buttons.addStretch()
        panel.addLayout(buttons)
        self.tabs = QTabWidget()
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Field", "Value"])
        self.tree.setColumnWidth(0, 280)
        self.json_view = QPlainTextEdit()
        self.json_view.setReadOnly(True)
        self.tabs.addTab(self.tree, "Result explorer")
        self.tabs.addTab(self.json_view, "JSON receipt")
        panel.addWidget(self.tabs, 1)
        self.splitter.addWidget(right)
        self.splitter.setStretchFactor(1, 1)
        layout.addWidget(self.splitter, 1)
        self.setCentralWidget(central)
        self.operations.currentRowChanged.connect(self.select_operation)
        self.operations.setCurrentRow(0)
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        splitter = self.settings.value("splitter")
        if splitter:
            self.splitter.restoreState(splitter)
        self.statusBar().showMessage("Ready · operations run in a background worker")

    def select_operation(self, row):
        while self.form.rowCount():
            self.form.removeRow(0)
        self.fields = {}
        operation = OPERATIONS[row]
        self.description.setText(operation.description + "\nEffect: " + operation.effect)
        defaults = inspect.signature(operation.function).parameters
        for name, spec in operation.inputs.items():
            default = defaults[name].default
            if spec["type"] == "boolean":
                field = QCheckBox("Allow unverified TLS for this local simulator read")
                field.setChecked(default is True)
            elif "enum" in spec:
                field = QComboBox()
                field.addItems(spec["enum"])
            elif spec["type"] in {"integer", "number"}:
                field = QSpinBox() if spec["type"] == "integer" else QDoubleSpinBox()
                field.setRange(spec.get("minimum", 0), spec.get("maximum", 100000))
                field.setValue(default if default is not inspect.Parameter.empty else (850 if name == "port" else 1))
            else:
                field = QLineEdit()
                if name in {"path", "left", "right", "cell", "executable"}:
                    field.setText(self.settings.value("path/" + name, ""))
                    wrapper = QWidget()
                    line = QHBoxLayout(wrapper)
                    line.setContentsMargins(0, 0, 0, 0)
                    line.addWidget(field)
                    browse = QPushButton("Browse…")
                    browse.clicked.connect(lambda checked=False, key=name, edit=field: self.browse(key, edit))
                    line.addWidget(browse)
                    self.form.addRow(name.replace("_", " ").capitalize(), wrapper)
                    self.fields[name] = field
                    continue
            self.fields[name] = field
            self.form.addRow(name.replace("_", " ").capitalize(), field)

    def browse(self, name, edit):
        operation = OPERATIONS[self.operations.currentRow()].name
        is_file = name in {"cell", "executable"} or operation in {"xml.inspect", "val3.analyze"}
        if is_file:
            selected, _ = QFileDialog.getOpenFileName(self, "Select source file", edit.text())
        else:
            selected = QFileDialog.getExistingDirectory(self, "Select project directory", edit.text())
        if selected:
            edit.setText(selected)

    def run_operation(self):
        if self.worker is not None:
            return
        arguments = {}
        for name, field in self.fields.items():
            if isinstance(field, QCheckBox):
                value = field.isChecked()
            elif isinstance(field, QComboBox):
                value = field.currentText()
            elif isinstance(field, (QSpinBox, QDoubleSpinBox)):
                value = field.value()
            else:
                value = field.text()
                if name in {"path", "left", "right", "cell", "executable"}:
                    self.settings.setValue("path/" + name, value)
            arguments[name] = value
        name = OPERATIONS[self.operations.currentRow()].name
        self.run_button.setEnabled(False)
        self.operations.setEnabled(False)
        self.statusBar().showMessage("Running " + name + "…")
        self.worker = Worker(name, arguments, self)
        self.worker.result.connect(self.show_result)
        self.worker.finished.connect(self.finish_worker)
        self.worker.start()

    def finish_worker(self):
        self.worker.deleteLater()
        self.worker = None
        self.run_button.setEnabled(True)
        self.operations.setEnabled(True)

    def show_result(self, result):
        self.last_result = result
        self.json_view.setPlainText(json.dumps(result, indent=2, ensure_ascii=False))
        self.tree.clear()
        # Bound visual items; the complete result remains in the JSON receipt.
        budget = [3000]
        def add(parent, key, value):
            if budget[0] <= 0:
                return
            budget[0] -= 1
            node = QTreeWidgetItem(parent, [str(key), "" if isinstance(value, (list, dict)) else str(value)])
            if isinstance(value, dict):
                for k, v in value.items():
                    add(node, k, v)
            elif isinstance(value, list):
                for k, v in enumerate(value):
                    add(node, k, v)
        for key, value in result.items():
            add(self.tree, key, value)
        self.tree.expandToDepth(1)
        self.save_button.setEnabled(True)
        self.statusBar().showMessage(("Complete" if result["ok"] else "Failed: " + result["error"]["message"]) +
                                     (" · Explorer limited to 3000 items; full receipt available" if budget[0] <= 0 else ""))

    def save_result(self):
        selected, _ = QFileDialog.getSaveFileName(self, "Save JSON receipt", "result.json", "JSON (*.json)")
        if selected:
            try:
                # QFileDialog handles an explicit overwrite choice for GUI saves.
                Path(selected).write_text(json.dumps(self.last_result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            except OSError as exc:
                QMessageBox.warning(self, "Could not save result", str(exc))

    def closeEvent(self, event):
        if self.worker is not None:
            self.statusBar().showMessage("Wait for the current bounded operation to finish before closing")
            event.ignore()
            return
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("splitter", self.splitter.saveState())
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    if sys.platform == "win32":
        app.setFont(QFont("Segoe UI", 10))
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
