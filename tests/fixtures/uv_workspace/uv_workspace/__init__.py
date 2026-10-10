from foo import hello as foo_hello  # declared workspace dep - ok
import pandas  # DEP102: not declared, available only via bar
