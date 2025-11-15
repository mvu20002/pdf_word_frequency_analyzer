# analyzer/__init__.py

"""
Core analysis package for the PDF Word Frequency Analyzer.

This module provides shared utilities (such as logging) and
serves as a namespace for reader, processor, and filter modules.
"""


def log_progress(message: str) -> None:
    """
    Simple logging helper used across the package.

    Args:
        message: Message string to be printed to stdout.
    """
    print(f"[LOG] {message}")
