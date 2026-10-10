import missing_package  # DEP001: declared nowhere and not installed
import numpy  # DEP003: only installed because qux declares pandas
import pandas  # declared dependency - ok
from bar2 import hello as bar_hello  # declared workspace dep `bar`, that exposes module `bar2` - ok


def hello() -> str:
    return bar_hello()
