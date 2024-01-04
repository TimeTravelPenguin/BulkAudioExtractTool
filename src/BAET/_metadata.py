import importlib.metadata


def app_version() -> str:
    return importlib.metadata.version("BAET")
