# vinayak/data/cleaner.py

from dataclasses import dataclass


@dataclass
class CleanerConfig:
    remove_nulls: bool = True
    normalize_dates: bool = True


class OHLCVValidationError(Exception):
    pass


def coerce_ohlcv(data):
    """
    Temporary stub to prevent crash.
    Replace with real cleaning logic later.
    """
    return data