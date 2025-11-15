# analyzer/filters.py

from collections import Counter
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

from langdetect import DetectorFactory, detect

# Ensure deterministic language detection
DetectorFactory.seed = 0


@lru_cache(maxsize=50000)
def _detect_language_cached(word: str) -> Optional[str]:
    """
    Cached wrapper around 'langdetect.detect' to avoid repeated expensive calls.

    Args:
        word: Input word whose language will be detected.

    Returns:
        ISO 639-1 language code (e.g. 'en', 'tr') or None if detection fails.
    """
    try:
        return detect(word)
    except Exception:
        return None


def filter_word_by_language(word: str, target_lang_codes: List[str]) -> bool:
    """
    Check whether the given word belongs to one of the target languages.

    Args:
        word: Input word.
        target_lang_codes: List of ISO 639-1 language codes to match.

    Returns:
        True if the detected language of 'word' is in target_lang_codes.
    """
    if len(word) < 3:
        return False

    detected_lang = _detect_language_cached(word)
    if detected_lang is None:
        return False
    return detected_lang in target_lang_codes


def filter_word_list(
    args: Tuple[List[str], set, Optional[List[str]]]
) -> List[str]:
    """
    Multiprocessing-safe word filtering function.

    This function is designed to be called from ProcessPoolExecutor using
    a single tuple argument for pickle compatibility.

    Args:
        args: A tuple of (raw_words, excluded_set, target_lang_codes)
              where:
              - raw_words: List of words to filter.
              - excluded_set: Set of words to skip.
              - target_lang_codes: Optional list of language codes.

    Returns:
        Filtered list of words.
    """
    raw_words, excluded_set, target_lang_codes = args
    filtered_words: List[str] = []

    has_lang_filter = bool(target_lang_codes)

    for word in raw_words:
        # Exclusion and length filter
        if word in excluded_set or len(word) < 2:
            continue

        # Language filter
        if has_lang_filter and target_lang_codes is not None:
            if not filter_word_by_language(word, target_lang_codes):
                continue

        filtered_words.append(word)

    return filtered_words


def filter_by_frequency_range(
    frequency_dict: Dict[str, int], min_freq: int, max_freq: int
) -> Dict[str, int]:
    """
    Filter a frequency dictionary by an inclusive frequency range.

    Args:
        frequency_dict: Dictionary mapping words to frequencies.
        min_freq: Minimum allowed frequency (inclusive).
        max_freq: Maximum allowed frequency (inclusive).

    Returns:
        Filtered frequency dictionary.
    """
    return {
        word: freq
        for word, freq in frequency_dict.items()
        if min_freq <= freq <= max_freq
    }


def filter_by_exact_frequency(
    frequency_dict: Dict[str, int], exact_freqs: List[int]
) -> Dict[str, int]:
    """
    Filter a frequency dictionary by specific exact frequency values.

    Args:
        frequency_dict: Dictionary mapping words to frequencies.
        exact_freqs: List of frequency values to keep.

    Returns:
        Filtered frequency dictionary.
    """
    exact_freqs_set = set(exact_freqs)
    return {
        word: freq for word, freq in frequency_dict.items() if freq in exact_freqs_set
    }


def count_frequencies(words: List[str]) -> Dict[str, int]:
    """
    Count frequencies of words using a Counter.

    Args:
        words: List of words.

    Returns:
        Dictionary mapping word to frequency.
    """
    return dict(Counter(words))
