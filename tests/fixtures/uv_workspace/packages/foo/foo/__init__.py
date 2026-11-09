import pandas  # DEP102: available only because bar declares it, not declared by foo


def hello() -> str:
    return "Hello from foo!"
