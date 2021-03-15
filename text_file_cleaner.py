# -*- coding:utf-8 -*-
import os

# 이 패치를 하면 print output이 buffering되는 문제가 있어 pyinstaller runtime에서만 적용
from text_filters import FilterBase


class TextFileCleaner():
    def __init__(self, path_list: list[str], filters: list[FilterBase]):
        self.path_list = path_list
        self.filters = filters
        self._num_excluded = 0
        self._total_lines = 0

    def get_total_file_lines(self):
        if not self._total_lines:
            self._total_lines = sum(map(
                lambda path: sum(1 for _ in open(path, encoding='utf-8')),
                self.path_list
            ))

        return self._total_lines

    def get_num_excluded(self):
        return self._num_excluded

    def process(self):
        for path in self.path_list:
            with open(path, encoding='utf-8') as in_file:
                out_filename = self.add_prefix(path, 'cleaned_')
                with open(out_filename, 'w', encoding='utf-8') as out_file:
                    for processed_lines in self.process_file(in_file, out_file):
                        yield processed_lines


    def add_prefix(self, path: str, prefix: str):
        head, tail = os.path.split(path)
        return f"{head}/{prefix}{tail}"

    def process_file(self, in_file, out_file):
        processed_lines = 0
        for line in in_file:
            processed_lines += 1

            for filter in self.filters:
                line = filter.filter(line)
                if not line:
                    break

            if line:
                out_file.write(line + '\n')
            else:
                self._num_excluded += 1

            if processed_lines >= 10000:
                yield processed_lines
                processed_lines = 0
        yield processed_lines
