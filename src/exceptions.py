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