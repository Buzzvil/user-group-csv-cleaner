# -*- coding:utf-8 -*-
import re
from abc import abstractmethod, ABC


class UUIDExtractorBase(ABC):
    @abstractmethod
    def extract(self, line):
        pass


class UUIDDashExtractor(UUIDExtractorBase):
    pattern = re.compile(r'[0-9a-fA-F]{32}')

    def extract(self, line):
        match = re.search(self.pattern, line)
        if match:
            matched_line = match.group()
            return matched_line[:8] + '-' + matched_line[8:12] + '-' + matched_line[12:16] + '-' + matched_line[16:20] + '-' + matched_line[20:]
        else:
            return None


class UUIDSearchExtractor(UUIDExtractorBase):
    uuid_pattern = re.compile(r'[a-fA-F\d]{8}\-[a-fA-F\d]{4}\-[a-fA-F\d]{4}-[a-fA-F\d]{4}-[a-fA-F\d]{12}')

    def extract(self, line):
        match = re.search(self.uuid_pattern, line)
        if match:
            return match.group()
        else:
            return None
