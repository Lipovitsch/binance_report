class BinanceReportException(Exception):
    pass


class PathError(BinanceReportException):
    pass


class DateError(BinanceReportException):
    pass


class CheckBoxError(BinanceReportException):
    pass


class SymbolsError(BinanceReportException):
    pass


class APIError(BinanceReportException):
    pass


class NBPAPIError(BinanceReportException):
    pass


class APIKeysError(BinanceReportException):
    pass


class DateRangeError(BinanceReportException):
    pass


class FileAccessError(BinanceReportException):
    pass
