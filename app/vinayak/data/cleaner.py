class CleanerConfig:
    pass


class OHLCVValidationError(Exception):
    pass


def coerce_ohlcv(data):
    return data