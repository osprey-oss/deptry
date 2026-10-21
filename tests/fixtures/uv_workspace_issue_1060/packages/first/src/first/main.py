import a  # DEP001: not declared by `first`
import click  # declared dependency (`b` in the issue) - ok
import second  # declared workspace dep - ok
from first import NAME  # import from itself - ok
