from foo import hello as foo_hello  # declared workspace dep - ok
from bar2 import hello as bar_hello  # DEP101: bar is a workspace sibling but not declared as a dep


def hello() -> str:
    return f"{foo_hello()} {bar_hello()}"
