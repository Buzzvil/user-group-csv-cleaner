# -*- coding:utf-8 -*-
import asyncio
import errno
import os
import signal
import sys
from functools import partial
from os.path import isfile, join
from pathlib import Path
from typing import List

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QListWidget, QPushButton, QVBoxLayout, QWidget, \
    QLabel, QProgressDialog, QMessageBox, QFileDialog, QCheckBox
from qasync import QEventLoop, asyncSlot

from csv_cleaner import CSVCleaner
from uuid_extractors import UUIDDashExtractor, UUIDSearchExtractor

APP_VERSION = '0.1.4'


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


# https://pyinstaller.readthedocs.io/en/stable/runtime-information.html#run-time-information
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    print('running in a PyInstaller bundle')
    log_path = str(Path.home()) + '/Library/Logs/User Group CSV Cleaner/log.txt'
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
else:
    print('running in a normal Python process')


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

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()

            links = self.urls_to_files(event.mimeData().urls())
            # 똑같은 파일 또 집어넣으면 중복 제거
            links = self.filter_duplicates(links, self.get_all_path())

            self.addItems(links)
        else:
            event.ignore()

    def get_all_path(self):
        path_list = []
        for index in range(self.count()):
            path_list.append(self.item(index).text())
        return path_list

    def urls_to_files(self, urls) -> List[str]:
        links = []
        for url in urls:
            # https://doc.qt.io/qt-5/qurl.html
            if url.isLocalFile():
                local_path = str(url.toLocalFile())
                if os.path.isdir(local_path):
                    for file_name in os.listdir(local_path):
                        full_path = join(local_path, file_name)
                        # Sub directory 및 숨김파일 제외
                        if isfile(full_path) and not file_name.startswith('.'):
                            links.append(full_path)
                else:
                    links.append(local_path)
            else:
                links.append(str(url.toString()))
        return links

    def filter_duplicates(self, links: List[str], existing_links: List[str]):
        return [l for l in links if l not in existing_links]


class CSVCleanerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(600, 400)

        self.setWindowTitle(f"User Group CSV Cleaner v{APP_VERSION}")
        layout = QVBoxLayout()

        # self.clear_btn.clicked signal에 연결하기 위해 미리 생성
        self.listbox_view = ListBoxWidget(self)

        self.process_btn = QPushButton('Process', self)
        self.process_btn.clicked.connect(self.process_list_widget)
        layout.addWidget(self.process_btn)

        self.clear_btn = QPushButton('Clear list', self)
        self.clear_btn.clicked.connect(self.listbox_view.clear)
        layout.addWidget(self.clear_btn)

        self.help_btn = QPushButton('Help', self)
        self.help_btn.clicked.connect(self.show_help)
        layout.addWidget(self.help_btn)

        self.merge_cb = QCheckBox('Make a singe file', self)
        layout.addWidget(self.merge_cb)

        self.label = QLabel(self)
        self.label.setText("Please drag & drop here")
        layout.addWidget(self.label)

        layout.addWidget(self.listbox_view)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def show_help(self):
        QMessageBox.about(
            self,
            "Help",
            """1. csv, xls, xlsx 파일을 지원합니다.
2. csv는 한 줄을 하나의 id로 처리하며 xls, xlsx는 컬럼이 여러개인 경우 각 컬럼을 별개의 id로 처리합니다.
3. 각 id를 처리하는 순서는 다음과 같습니다.
- 처음으로 발견된 정상 UUID(IFA) 문자열을 찾아 추출합니다. (prefix, suffix 동시 제거 효과)
- 추출이 실패한 경우 처음으로 발견된 연속된 32자의 영문자열을 찾아 대시를 삽입하여 UUID로 만듭니다.
e.g.) "00003469153d4b9a996ec04e8c84e52ea"
-> 00003469-153d-4b9a-996e-c04e8c84e52e
"""
        )

    @asyncSlot()
    async def process_list_widget(self):
        path_list = self.listbox_view.get_all_path()
        cleaner = CSVCleaner(
            path_list=path_list,
            extractors=[
                UUIDSearchExtractor(),
                UUIDDashExtractor(),
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
            merged_path = QFileDialog.getSaveFileName(
                None,
                'Save File',
                os.path.join(os.path.expanduser('~'), 'downloads/user_group.csv')
            )[0]
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

    text_cleaner_app = CSVCleanerApp()
    text_cleaner_app.show()

    print("Running...")

    # https://github.com/CabbageDevelopment/qasync/blob/master/examples/aiohttp_fetch.py
    with loop:
        sys.exit(loop.run_forever())
