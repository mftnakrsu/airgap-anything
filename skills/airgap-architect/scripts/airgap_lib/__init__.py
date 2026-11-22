"""Shared code for the airgap-architect scripts.

Importing this package checks the Python version first, so every script
fails with a clear message on an interpreter older than 3.11.
"""
import sys

MINIMUM_PYTHON = (3, 11)
EXIT_ENVIRONMENT = 3


def check_python(version_info=None):
    """Return an error message when the interpreter is too old, else None."""
    version = tuple((version_info or sys.version_info)[:2])
    if version < MINIMUM_PYTHON:
        return "airgap-architect needs Python %d.%d or newer (found %d.%d)." % (
            MINIMUM_PYTHON + version
        )
    return None


_message = check_python()
if _message:
    sys.stderr.write(_message + "\n")
    raise SystemExit(EXIT_ENVIRONMENT)
