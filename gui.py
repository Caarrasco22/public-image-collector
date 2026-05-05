#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gui.py — Ventana principal con PySide6.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QIcon, QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from scraper import Scraper


class Worker(QThread):
    log = Signal(str)
    progress = Signal(int, int)
    finished_analysis = Signal(list)
    finished_download = Signal(list)

    def __init__(self, mode, scraper, **kwargs):
        super().__init__()
        self.mode = mode
        self.scraper = scraper
        self.kwargs = kwargs

    def run(self):
        try:
            if self.mode == "analyze":
                url = self.kwargs["url"]
                results = self.scraper.analyze(url)
                self.finished_analysis.emit(results)
            elif self.mode == "download":
                images = self.kwargs["images"]
                folder = self.kwargs["folder"]
                downloaded = self.scraper.download(
                    images,
                    folder,
                    on_progress=lambda cur, tot: self.progress.emit(cur, tot),
                    on_log=lambda msg: self.log.emit(msg),
                )
                self.finished_download.emit(downloaded)
        except Exception as e:
            self.log.emit(f"Error: {e}")
            if self.mode == "analyze":
                self.finished_analysis.emit([])
            else:
                self.finished_download.emit([])


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Public Image Collector")
        self.resize(900, 700)

        self.scraper = Scraper()
        self.worker = None
        self.current_images = []

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Disclaimer
        disclaimer = QLabel(
            "<b>Aviso / Warning:</b> Usa esta herramienta solo en páginas públicas "
            "donde tengas permiso para descargar contenido.<br>"
            "Use this tool only on public pages where you have permission to download content."
        )
        disclaimer.setWordWrap(True)
        disclaimer.setStyleSheet("color: #555; font-size: 12px;")
        layout.addWidget(disclaimer)

        # URL row
        url_row = QHBoxLayout()
        url_row.addWidget(QLabel("URL:"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://ejemplo.com/galeria")
        url_row.addWidget(self.url_input, 1)
        self.btn_analyze = QPushButton("Analizar / Analyze")
        self.btn_analyze.setStyleSheet("padding: 6px 16px;")
        self.btn_analyze.clicked.connect(self.start_analysis)
        url_row.addWidget(self.btn_analyze)
        layout.addLayout(url_row)

        # Destination folder
        folder_row = QHBoxLayout()
        folder_row.addWidget(QLabel("Destino / Destination:"))
        self.folder_input = QLineEdit()
        default_folder = str(Path.home() / "Downloads" / "public-image-collector")
        self.folder_input.setText(default_folder)
        folder_row.addWidget(self.folder_input, 1)
        btn_browse = QPushButton("Examinar / Browse")
        btn_browse.clicked.connect(self.pick_folder)
        folder_row.addWidget(btn_browse)
        layout.addLayout(folder_row)

        # Select all
        self.chk_select_all = QCheckBox("Seleccionar todas / Select all")
        self.chk_select_all.setChecked(True)
        self.chk_select_all.stateChanged.connect(self.toggle_select_all)
        layout.addWidget(self.chk_select_all)

        # Image list
        self.list_images = QListWidget()
        self.list_images.setIconSize(QSize(64, 64))
        layout.addWidget(self.list_images, 1)

        # Progress
        self.progress = QProgressBar()
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        # Buttons row
        btn_row = QHBoxLayout()
        self.btn_download = QPushButton("Descargar seleccionadas / Download selected")
        self.btn_download.setStyleSheet("padding: 8px 20px; font-weight: bold;")
        self.btn_download.clicked.connect(self.start_download)
        btn_row.addWidget(self.btn_download)

        self.btn_cancel = QPushButton("Cancelar / Cancel")
        self.btn_cancel.clicked.connect(self.cancel_operation)
        self.btn_cancel.setEnabled(False)
        btn_row.addWidget(self.btn_cancel)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Log
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(500)
        self.log.setPlaceholderText("Log de actividad / Activity log...")
        self.log.setStyleSheet("font-family: monospace; font-size: 11px;")
        layout.addWidget(self.log, 0)

        self.setLayout(layout)

    def pick_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta / Select folder", self.folder_input.text())
        if folder:
            self.folder_input.setText(folder)

    def log_msg(self, msg):
        self.log.appendPlainText(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    def start_analysis(self):
        url = self.url_input.text().strip()
        if not url.startswith(("http://", "https://")):
            QMessageBox.warning(self, "URL inválida", "Introduce una URL válida que empiece por http:// o https://")
            return

        self.list_images.clear()
        self.current_images.clear()
        self.progress.setValue(0)
        self.set_controls_enabled(False, mode="analyze")
        self.log_msg(f"Analizando: {url}")

        self.worker = Worker("analyze", self.scraper, url=url)
        self.worker.log.connect(self.log_msg)
        self.worker.finished_analysis.connect(self.on_analysis_done)
        self.worker.start()

    def on_analysis_done(self, images):
        self.current_images = images
        for img in images:
            item = QListWidgetItem()
            item.setText(f"{img.filename}  |  {img.width or '?'}x{img.height or '?'}  |  {img.url[:80]}")
            item.setCheckState(Qt.Checked if img.selected else Qt.Unchecked)
            item.setData(Qt.UserRole, img)

            # Thumbnail
            thumb = self.scraper.generate_thumb(img, size=(64, 64))
            if thumb:
                qimg = QImage(thumb.tobytes("raw", "RGB"), thumb.width, thumb.height, thumb.width * 3, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qimg)
                item.setIcon(QIcon(pixmap))

            self.list_images.addItem(item)

        self.log_msg(f"Imágenes detectadas: {len(images)}")
        self.set_controls_enabled(True)

    def toggle_select_all(self, state):
        for i in range(self.list_images.count()):
            item = self.list_images.item(i)
            item.setCheckState(Qt.Checked if state == Qt.Checked else Qt.Unchecked)
            img = item.data(Qt.UserRole)
            if img:
                img.selected = item.checkState() == Qt.Checked

    def start_download(self):
        selected = []
        for i in range(self.list_images.count()):
            item = self.list_images.item(i)
            img = item.data(Qt.UserRole)
            if img:
                img.selected = item.checkState() == Qt.Checked
                if img.selected:
                    selected.append(img)

        if not selected:
            QMessageBox.information(self, "Sin selección", "No has seleccionado ninguna imagen.")
            return

        folder = self.folder_input.text().strip()
        url = self.url_input.text().strip()
        parsed = urlparse(url)
        domain = parsed.netloc.replace(":", "_")
        date_str = datetime.now().strftime("%Y-%m-%d")
        dest = Path(folder) / f"{domain}_{date_str}"

        self.progress.setValue(0)
        self.progress.setMaximum(len(selected))
        self.set_controls_enabled(False, mode="download")
        self.log_msg(f"Descargando {len(selected)} imagen(es) a: {dest}")

        self.worker = Worker("download", self.scraper, images=selected, folder=str(dest))
        self.worker.log.connect(self.log_msg)
        self.worker.progress.connect(lambda cur, tot: self.progress.setValue(cur))
        self.worker.finished_download.connect(self.on_download_done)
        self.worker.start()

    def on_download_done(self, paths):
        self.log_msg(f"Descarga completada: {len(paths)} archivo(s).")
        self.set_controls_enabled(True)
        if paths:
            QMessageBox.information(self, "Completado", f"Se descargaron {len(paths)} imagen(es).")

    def cancel_operation(self):
        if self.worker and self.worker.isRunning():
            self.scraper.cancelled = True
            self.log_msg("Cancelando...")
            self.worker.wait(3000)
        self.set_controls_enabled(True)

    def set_controls_enabled(self, enabled, mode=None):
        self.btn_analyze.setEnabled(enabled)
        self.btn_download.setEnabled(enabled)
        self.btn_cancel.setEnabled(not enabled)
        self.url_input.setEnabled(enabled)
        self.folder_input.setEnabled(enabled)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Public Image Collector")
    app.setApplicationDisplayName("Public Image Collector")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
