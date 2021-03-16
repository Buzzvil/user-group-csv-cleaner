# -*- coding:utf-8 -*-
import re
from abc import abstractmethod, ABC


uuid_patter = re.compile('^[a-fA-F\d]{8}\-[a-fA-F\d]{4}\-[a-fA-F\d]{4}-[a-fA-F\d]{4}-[a-fA-F\d]{12}$')


def _is_valid_uuid(line):
    if re.match(uuid_patter, line):
        return line
    else:
        return None


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


class UUIDSuffixRemoveFilter(FilterBase):
    def filter(self, line):
        if _is_valid_uuid(line[:36]):
            return line[:36]
        return line


class UUIDPrefixRemoveFilter(FilterBase):
    def filter(self, line):
        if _is_valid_uuid(line[-36:]):
            return line[-36:]
        return line


class UUIDDashFilter(FilterBase):
    p = re.compile('^[0-9a-fA-F]{32}$')

    def filter(self, line):
        if re.match(self.p, line):
            return line[:8] + '-' + line[8:12] + '-' + line[12:16] + '-' + line[16:20] + '-' + line[20:]
        return line


class ValidUUIDFilter(FilterBase):

    def filter(self, line):
        if _is_valid_uuid(line):
            return line
        else:
            return None
