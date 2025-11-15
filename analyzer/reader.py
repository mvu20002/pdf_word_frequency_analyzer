# analyzer/reader.py

import os
import threading
from typing import Callable, List

from pypdf import PdfReader

from . import log_progress


def find_pdf_files(input_path: str) -> List[str]:
    """
    Discover PDF files based on the given input path.

    Args:
        input_path: Either a path to a single PDF file or a directory
                    containing one or more PDF files.

    Returns:
        List of absolute paths to PDF files.

    Raises:
        ValueError: If the input path is neither a PDF file nor a directory.
    """
    if os.path.isfile(input_path) and input_path.lower().endswith(".pdf"):
        return [os.path.abspath(input_path)]

    if os.path.isdir(input_path):
        directory = os.path.abspath(input_path)
        return [
            os.path.join(directory, entry)
            for entry in os.listdir(directory)
            if entry.lower().endswith(".pdf")
        ]

    raise ValueError(f"Invalid input path or file type: {input_path}")


def _read_single_pdf(
    pdf_file_path: str,
    total_count: int,
    counter: "threading.Lock",  # for type-hint clarity, counter is guarded by lock
    counter_lock: threading.Lock,
    texts: List[str],
    texts_lock: threading.Lock,
    logger: Callable[[str], None],
) -> None:
    """
    Read a single PDF file and append its extracted text into a shared list.

    This function is intended to be used with multithreading and uses
    local locks for safe updates.

    Args:
        pdf_file_path: Path to the PDF file.
        total_count: Total number of PDF files being processed.
        counter: A simple integer wrapped via 'nonlocal' usage in the caller,
                 guarded by 'counter_lock'.
        counter_lock: Threading lock for safely updating the progress counter.
        texts: Shared list to store extracted text.
        texts_lock: Threading lock for safely appending to 'texts'.
        logger: Logging function.
    """
    file_name = os.path.basename(pdf_file_path)

    try:
        reader = PdfReader(pdf_file_path)
        local_text_parts = []

        for page in reader.pages:
            try:
                text = page.extract_text() or " "
            except Exception:
                # If a single page fails, skip it but continue with the rest.
                text = " "
            local_text_parts.append(text)

        local_text = " ".join(local_text_parts)

        with texts_lock:
            texts.append(local_text)

        with counter_lock:
            counter.value += 1  # type: ignore[attr-defined]
            logger(
                f"File read: {file_name}. Progress: {counter.value}/{total_count}"  # type: ignore[attr-defined]
            )

    except Exception as exc:
        logger(f"ERROR: Failed to read file '{file_name}': {exc}")

        # Even on error, we still update progress to avoid stalling.
        with counter_lock:
            counter.value += 1  # type: ignore[attr-defined]
            logger(
                f"File skipped due to error. Progress: {counter.value}/{total_count}"  # type: ignore[attr-defined]
            )


class _Counter:
    """
    Simple mutable integer-like object used for tracking progress
    across threads without using global state.
    """

    def __init__(self) -> None:
        self.value = 0


def read_pdfs_in_parallel(
    pdf_file_paths: List[str],
    max_workers_io: int = 8,
    logger: Callable[[str], None] = log_progress,
) -> str:
    """
    Read multiple PDF files in parallel using a thread pool.

    Args:
        pdf_file_paths: List of PDF file paths to process.
        max_workers_io: Max number of threads to use for I/O operations.
        logger: Logging function.

    Returns:
        A single concatenated string containing all extracted text.
    """
    if not pdf_file_paths:
        return ""

    from concurrent.futures import ThreadPoolExecutor

    texts: List[str] = []
    texts_lock = threading.Lock()

    counter = _Counter()
    counter_lock = threading.Lock()
    total_count = len(pdf_file_paths)

    logger(f"Total files to process: {total_count}")
    logger(f"PDFs are being read in parallel using {max_workers_io} threads...")

    with ThreadPoolExecutor(max_workers=max_workers_io) as executor:
        for pdf_path in pdf_file_paths:
            executor.submit(
                _read_single_pdf,
                pdf_path,
                total_count,
                counter,
                counter_lock,
                texts,
                texts_lock,
                logger,
            )

    return " ".join(texts)
