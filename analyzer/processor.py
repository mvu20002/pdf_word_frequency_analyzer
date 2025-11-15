# analyzer/processor.py

import os
import re
import time
import itertools
import json
import csv
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, List, Optional, Tuple

from . import log_progress
from .reader import find_pdf_files, read_pdfs_in_parallel
from .filters import (
    filter_word_list,
    filter_by_exact_frequency,
    filter_by_frequency_range,
    count_frequencies,
)


def calculate_word_frequency_and_filter(
    input_path: str,
    excluded_words: List[str],
    target_lang_codes: Optional[List[str]] = None,
    min_freq: Optional[int] = None,
    max_freq: Optional[int] = None,
    exact_freqs: Optional[List[int]] = None,
    max_workers_io: int = 8,
    max_workers_cpu: Optional[int] = None,
) -> Tuple[int, Dict[str, int]]:
    """
    Main analysis function.

    This function orchestrates:
    1. PDF discovery
    2. Parallel PDF reading (I/O-bound)
    3. Word extraction and multiprocessing-based filtering (CPU-bound)
    4. Frequency filtering

    Args:
        input_path: Path to a single PDF file or directory of PDFs.
        excluded_words: List of words to exclude from analysis.
        target_lang_codes: Optional list of ISO 639-1 language codes to keep.
        min_freq: Optional minimum frequency (inclusive) for filtering.
        max_freq: Optional maximum frequency (inclusive) for filtering.
        exact_freqs: Optional list of exact frequency values to keep.
        max_workers_io: Max number of threads for PDF reading.
        max_workers_cpu: Max number of processes for word filtering; defaults to CPU count.

    Returns:
        A tuple of:
        - total_valid_word_count: Number of words after all filtering.
        - filtered_frequency_dict: Dictionary mapping words to their frequencies.
    """
    start_time = time.time()

    # --- Phase 0: Discover PDF files ---
    try:
        pdf_file_paths = find_pdf_files(input_path)
    except ValueError as exc:
        log_progress(f"Error: {exc}")
        return 0, {}

    if not pdf_file_paths:
        log_progress("Error: No PDF files found for processing.")
        return 0, {}

    # --- Phase 1: Parallel PDF Reading (I/O) ---
    all_text = read_pdfs_in_parallel(
        pdf_file_paths=pdf_file_paths,
        max_workers_io=max_workers_io,
        logger=log_progress,
    )

    read_end_time = time.time()
    log_progress(f"Reading complete. Duration: {read_end_time - start_time:.2f} s.")

    if not all_text.strip():
        log_progress("Warning: No text extracted from PDF files.")
        return 0, {}

    # --- Phase 2: Word Processing and Parallel Filtering (CPU) ---
    log_progress("Starting word processing and filtering (Multiprocessing)...")

    # Basic word tokenization (keeps alphanumeric and underscore)
    raw_words: List[str] = re.findall(r"\b\w+\b", all_text.lower(), re.UNICODE)

    # Normalize excluded words to lowercase
    excluded_set = set(word.lower() for word in excluded_words)

    num_processes = max_workers_cpu or os.cpu_count() or 4
    chunk_size = max(1, len(raw_words) // num_processes + 1)

    word_chunks = [
        raw_words[i : i + chunk_size] for i in range(0, len(raw_words), chunk_size)
    ]

    arguments = [
        (chunk, excluded_set, target_lang_codes) for chunk in word_chunks
    ]

    with ProcessPoolExecutor(max_workers=num_processes) as executor:
        results = executor.map(filter_word_list, arguments)
        filtered_words = list(itertools.chain.from_iterable(results))

    processing_end_time = time.time()
    log_progress(
        f"Processing complete. Duration: {processing_end_time - read_end_time:.2f} s."
    )

    total_valid_word_count = len(filtered_words)
    word_frequency = count_frequencies(filtered_words)

    # --- Phase 3: Frequency Filtering ---
    if exact_freqs:
        final_frequency = filter_by_exact_frequency(word_frequency, exact_freqs)
    elif min_freq is not None or max_freq is not None:
        min_f = min_freq if min_freq is not None else 0
        max_f = max_freq if max_freq is not None else float("inf")
        final_frequency = filter_by_frequency_range(word_frequency, min_f, max_f)
    else:
        final_frequency = word_frequency

    return total_valid_word_count, final_frequency


def write_output(
    frequency_dict: Dict[str, int],
    total_count: int,
    output_format: str,
    filename: Optional[str],
) -> None:
    """
    Write the frequency dictionary to a file in the desired format.

    Args:
        frequency_dict: Dictionary mapping words to frequencies.
        total_count: Total number of valid words considered.
        output_format: One of 'txt', 'csv', or 'json'.
        filename: Output file name (with path). If None or empty, a default name is used.
    """
    # Sort by frequency (descending)
    sorted_data = sorted(frequency_dict.items(), key=lambda item: item[1], reverse=True)

    if not filename:
        filename = f"word_analysis_output.{output_format}"

    # Ensure output directory exists (if a directory is included in filename)
    directory = os.path.dirname(filename)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

    if output_format == "txt":
        with open(filename, "w", encoding="utf-8") as handle:
            handle.write("--- Word Analysis Results ---\n")
            handle.write(f"Total Valid Word Count: {total_count}\n")
            handle.write("=" * 35 + "\n")
            handle.write(f"{'Word':<25}{'Frequency':<10}\n")
            handle.write("-" * 35 + "\n")
            for word, freq in sorted_data:
                handle.write(f"{word:<25}{freq:<10}\n")

        print(f"\n✅ Results successfully written to {filename} in TXT format.")

    elif output_format == "csv":
        with open(filename, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["Word", "Frequency"])
            writer.writerows(sorted_data)

        print(f"\n✅ Results successfully written to {filename} in CSV format.")

    elif output_format == "json":
        output_data = {
            "metadata": {
                "total_valid_word_count": total_count,
                "analysis_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
            "frequency_list": [
                {"word": word, "frequency": freq} for word, freq in sorted_data
            ],
        }

        with open(filename, "w", encoding="utf-8") as handle:
            json.dump(output_data, handle, ensure_ascii=False, indent=4)

        print(f"\n✅ Results successfully written to {filename} in JSON format.")

    else:
        print(f"Error: Unsupported output format: {output_format}")
