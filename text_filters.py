# -*- coding:utf-8 -*-
import re
from abc import abstractmethod, ABC


class FilterBase(ABC):
    @abstractmethod
    def filter(self, line):
        pass


class StripQuotesFilter(FilterBase):
    def filter(self, line):
        return line.strip('"')


class StripWhiteSpaceFilter(FilterBase):
    def filter(self, line):
        return line.strip(' \n\t')


class UUIDDashFilter(FilterBase):
    p = re.compile('^[0-9a-fA-F]{32}$')

    def filter(self, line):
        if re.match(self.p, line):
            return line[:8] + '-' + line[8:12] + '-' + line[12:16] + '-' + line[16:20] + '-' + line[20:]
        return line


class ValidUUIDFilter(FilterBase):
    p = re.compile('^[a-fA-F\d]{8}\-[a-fA-F\d]{4}\-[a-fA-F\d]{4}-[a-fA-F\d]{4}-[a-fA-F\d]{12}$')

    def filter(self, line):
        if re.match(self.p, line):
            return line
        else:
            return None
