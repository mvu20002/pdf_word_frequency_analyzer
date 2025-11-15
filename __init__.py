# __init__.py

"""
Top-level package initializer for the PDF Word Frequency Analyzer.

This file exposes core analysis functions at the root package level
for convenient programmatic use.
"""

from analyzer.processor import calculate_word_frequency_and_filter, write_output

__all__ = [
    "calculate_word_frequency_and_filter",
    "write_output",
]
