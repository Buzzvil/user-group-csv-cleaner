# -*- coding:utf-8 -*-
import contextlib
import os
import zipfile
from io import BytesIO, TextIOWrapper
from zipfile import ZipFile

import pandas as pd

from text_filters import FilterBase


def excel_generator(path):
    df = pd.read_excel(path, header=None)
    for _, row in df.iterrows():
        for _, value in row.iteritems():
            yield str(value)


@contextlib.contextmanager
def csv_excel_reader(path):
    if path.endswith('xls') or path.endswith('xlsx'):
        file = excel_generator(path)
        yield file
    else:
        file = open(path, encoding='utf-8')
        yield file
        file.close()


class TextFileCleaner():
    def __init__(self, path_list: list[str], filters: list[FilterBase]):
        self.path_list = path_list
        self.filters = filters
        self._num_excluded = 0
        self._total_lines = 0

    def get_single_file_lines(self, path):
        with csv_excel_reader(path) as file:
            return sum(1 for _ in file)

    def get_total_file_lines(self):
        if not self._total_lines:
            self._total_lines = sum(map(
                lambda path: self.get_single_file_lines(path),
                self.path_list
            ))

        return self._total_lines

    def get_num_excluded(self):
        return self._num_excluded

    def get_suffixed_filename(self, path, index):
        filename, file_extension = os.path.splitext(path)
        if file_extension:
            return '{}({}){}'.format(filename, index, file_extension)
        else:
            return '{}({}})'.format(filename, index)

    def get_none_duplicated_path(self, path):
        if not os.path.exists(path):
            return path
        for i in range(1, 100):
            new_path = self.get_suffixed_filename(path, i)
            if not os.path.exists(new_path):
                return new_path
        raise Exception("Too many duplicated files")

    def process(self):
        for path in self.path_list:
            with csv_excel_reader(path) as in_file:
                out_filename = self.add_prefix(path, 'cleaned_').replace('.xlsx', '.csv').replace('.xls', '.csv')
                out_filename = self.get_none_duplicated_path(out_filename)
                with open(out_filename, 'w', encoding='utf-8') as out_file:
                    for processed_lines in self.process_file(in_file, out_file):
                        yield processed_lines

    def process_merge(self, out_path):
        with open(out_path, 'w', encoding='utf-8') as out_file:
            for in_path in self.path_list:
                with csv_excel_reader(in_path) as in_file:
                    for processed_lines in self.process_file(in_file, out_file):
                        yield processed_lines

    # 압축된 파일 끝에 데이터 몇줄 잘리는 문제 해결 필요
    def process_merge_compress(self, out_path):
        archive = BytesIO()
        with ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as zip_archive:
            with zip_archive.open('original.txt', 'w') as zip_dest_file:
                text_zip_dest_file = TextIOWrapper(zip_dest_file, encoding='utf-8', newline='')
                for in_path in self.path_list:
                    with open(in_path, encoding='utf-8') as in_file:
                        for processed_lines in self.process_file(in_file=in_file, out_file=text_zip_dest_file):
                            yield processed_lines

        with open(out_path, 'wb') as f:
            f.write(archive.getbuffer())

        archive.close()

    def add_prefix(self, path: str, prefix: str):
        head, tail = os.path.split(path)
        return f"{head}/{prefix}{tail}"

    def process_file(self, in_file, out_file):
        processed_lines = 0
        for line in in_file:
            processed_lines += 1

            filtered_line = None
            for filter in self.filters:
                filtered_line = filter.filter(line)
                if filtered_line:
                    break

            if filtered_line:
                out_file.write(filtered_line + '\n')
            else:
                self._num_excluded += 1

            if processed_lines >= 10000:
                yield processed_lines
                processed_lines = 0
        yield processed_lines
