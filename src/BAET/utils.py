import datetime


def micro_to_hhmmss(micro: float) -> str:
    """Convert milliseconds to HH:MM:SS format."""
    return str(datetime.timedelta(microseconds=micro))


if __name__ == "__main__":
    ms = 4007829000.0
    print(micro_to_hhmmss(ms))
