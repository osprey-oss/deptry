from bar2.greeting import GREETING  # own module in a `src` layout, not named after the package - ok


def hello() -> str:
    return GREETING
