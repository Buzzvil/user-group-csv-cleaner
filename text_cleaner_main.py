# -*- coding:utf-8 -*-
import asyncio
import errno
import os
import signal
import sys
from functools import partial
from os.path import isfile, join
from pathlib import Path

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QListWidget, QPushButton, QVBoxLayout, QWidget, \
    QLabel, QProgressDialog, QMessageBox, QFileDialog, QCheckBox
from qasync import QEventLoop, asyncSlot

# 이 패치를 하면 print output이 buffering되는 문제가 있어 pyinstaller runtime에서만 적용
from text_file_cleaner import TextFileCleaner
from text_filters import StripWhiteSpaceFilter, StripQuotesFilter, UUIDDashFilter, ValidUUIDFilter

APP_VERSION = '0.0.2'
DEBUG = False


# https://stackoverflow.com/questions/107705/disable-output-buffering
class Unbuffered(object):
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
    def writelines(self, datas):
        self.stream.writelines(datas)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)


if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    log_path = str(Path.home()) + '/Library/Logs/Text cleaner/log.txt'
    if not os.path.exists(os.path.dirname(log_path)):
        try:
            os.makedirs(os.path.dirname(log_path))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    # encoding설정 안하면 pyinstaller로 만든 실행파일에서 unicode print시 encoding에러 발생
    output = Unbuffered(open(log_path, 'w+', encoding='utf-8'))
    sys.stdout = output
    sys.stderr = output


class ListBoxWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.resize(600, 600)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def get_all_path(self):
        path_list = []
        for index in range(self.count()):
            path_list.append(self.item(index).text())
        return path_list

    def urls_to_files(self, urls) -> list[str]:
        links = []
        for url in urls:
            # https://doc.qt.io/qt-5/qurl.html
            if url.isLocalFile():
                local_path = str(url.toLocalFile())
                if os.path.isdir(local_path):
                    for file_name in os.listdir(local_path):
                        full_path = join(local_path, file_name)
                        if isfile(full_path) and not file_name.startswith('.'):
                            links.append(full_path)
                else:
                    links.append(local_path)
            else:
                links.append(str(url.toString()))
        return links

    def filter_duplicates(self, links: list[str], existing_links: list[str]):
        return [l for l in links if l not in existing_links]

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()

            links = self.urls_to_files(event.mimeData().urls())
            links = self.filter_duplicates(links, self.get_all_path())

            self.addItems(links)
        else:
            event.ignore()


class AppDemo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(600, 400)

        self.setWindowTitle(f"User group text cleaner v{APP_VERSION}")
        layout = QVBoxLayout()

        self.process_btn = QPushButton('Process', self)
        self.process_btn.clicked.connect(self.process_list_widget)
        layout.addWidget(self.process_btn)

        self.clear_btn = QPushButton('Clear list', self)
        self.clear_btn.clicked.connect(self.clear_list_widget)
        layout.addWidget(self.clear_btn)

        self.merge_cb = QCheckBox('Merge', self)
        layout.addWidget(self.merge_cb)

        self.label = QLabel(self)
        self.label.setText("Please drag & drop here")
        layout.addWidget(self.label)

        self.listbox_view = ListBoxWidget(self)
        layout.addWidget(self.listbox_view)

        if DEBUG:
            self.debugLabel = QLabel(self)
            self.debugLabel.setText('Debug console')
            layout.addWidget(self.debugLabel)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def clear_list_widget(self):
        self.listbox_view.clear()

    @asyncSlot()
    async def process_list_widget(self):
        path_list = self.listbox_view.get_all_path()
        cleaner = TextFileCleaner(
            path_list=path_list,
            filters=[
                StripWhiteSpaceFilter(),
                StripQuotesFilter(),
                UUIDDashFilter(),
                ValidUUIDFilter(),
            ]
        )

        if not cleaner.get_total_file_lines():
            QMessageBox.warning(
                self,
                "Warning",
                "No files to process",
            )
            return

        if self.merge_cb.isChecked():
            merged_path = QFileDialog.getSaveFileName(None, 'Save File', '/Users/jeseo/Downloads/merged.csv')[0]
            if not merged_path:
                print("Save file not selected")
                return
            process_func = partial(cleaner.process_merge, merged_path)
        else:
            process_func = cleaner.process

        self.progress = QProgressDialog('Work in progress', 'Cancel', 0, cleaner.get_total_file_lines(), self)
        self.progress.setWindowTitle("Generating files...")
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.show()
        self.progress.setValue(0)

        print(f"Process {path_list} total_file_lines {cleaner.get_total_file_lines()}")
        total_processed_lines = 0

        for processed_lines in process_func():
            total_processed_lines += processed_lines
            print(f'processed_lines {total_processed_lines}')
            self.progress.setValue(total_processed_lines)
            # Progress bar update를 위해 제어권 놓아주기
            await asyncio.sleep(0)
            if self.progress.wasCanceled():
                print("Process canceled")
                return

        QMessageBox.about(
            self,
            "Done",
            "\n".join([
                f"Total lines {cleaner.get_total_file_lines()}",
                f"Excluded lines {cleaner.get_num_excluded()}",
            ]),
        )


# https://stackoverflow.com/questions/4938723/what-is-the-correct-way-to-make-my-pyqt-application-quit-when-killed-from-the-co
def sigint_handler(*args):
    """Handler for the SIGINT signal."""
    sys.stderr.write('\r')
    QApplication.quit()


if __name__ == '__main__':
    signal.signal(signal.SIGINT, sigint_handler)
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # https://stackoverflow.com/questions/4938723/what-is-the-correct-way-to-make-my-pyqt-application-quit-when-killed-from-the-co
    timer = QTimer()
    timer.start(100)  # You may change this if you wish.
    timer.timeout.connect(lambda: None)  # Let the interpreter run each 500 ms.

    demo = AppDemo()
    demo.show()

    print("Running...")

    # https://github.com/CabbageDevelopment/qasync/blob/master/examples/aiohttp_fetch.py
    with loop:
        sys.exit(loop.run_forever())
