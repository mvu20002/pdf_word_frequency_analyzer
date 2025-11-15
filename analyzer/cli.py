# analyzer/cli.py

import argparse
import os
from typing import List, Optional

from . import log_progress
from .processor import calculate_word_frequency_and_filter, write_output


def parse_args() -> argparse.Namespace:
    """
    Configure and parse command-line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="PDF Folder/File Word Frequency Analyzer (Optimized with Multiprocessing).",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # 1. Input (Required)
    parser.add_argument(
        "input",
        type=str,
        help="Path to the PDF file or the folder containing PDF files for analysis.",
    )

    # 2. Excluded Words
    parser.add_argument(
        "-e",
        "--exclude",
        type=str,
        nargs="+",
        default=[],
        help="Words to exclude, specified directly (e.g., -e the and is).",
    )
    parser.add_argument(
        "-ef",
        "--exclude-file",
        type=str,
        help="Path to a TXT file containing words to exclude, one word per line.",
    )

    # 3. Frequency Specification
    freq_group = parser.add_mutually_exclusive_group()
    freq_group.add_argument(
        "-r",
        "--freq-range",
        type=int,
        nargs=2,
        metavar=("MIN", "MAX"),
        help="Specify a frequency range (e.g., -r 5 10).",
    )
    freq_group.add_argument(
        "-ex",
        "--exact-freq",
        type=int,
        nargs="+",
        help="Select specific exact frequency values (e.g., -ex 3 7).",
    )

    # 4. Target Language
    parser.add_argument(
        "-l",
        "--lang",
        type=str,
        nargs="+",
        default=[],
        help="One or more target language codes (ISO 639-1). "
        "If empty, no language filter is applied (e.g., -l en tr).",
    )

    # 5. Output Format
    parser.add_argument(
        "-o",
        "--output-format",
        type=str,
        default="txt",
        choices=["txt", "csv", "json"],
        help="Output file format: txt, csv, or json (Default: txt).",
    )

    # 6. Output Filename
    parser.add_argument(
        "-fn",
        "--filename",
        type=str,
        help="The name and path for the output file. "
        "If omitted, a default filename is used.",
    )

    return parser.parse_args()


def load_excluded_words(
    inline_excluded: List[str], excluded_file: Optional[str]
) -> List[str]:
    """
    Combine inline excluded words and words loaded from a file.

    Args:
        inline_excluded: Words passed directly via CLI.
        excluded_file: Optional path to a text file with one word per line.

    Returns:
        Combined list of all excluded words (lowercased).
    """
    excluded_list = [word.lower() for word in inline_excluded]

    if excluded_file:
        if not os.path.isfile(excluded_file):
            print(f"Error: Excluded words file not found at: {excluded_file}")
            return excluded_list

        try:
            with open(excluded_file, "r", encoding="utf-8") as handle:
                file_words = [
                    line.strip().lower() for line in handle.readlines() if line.strip()
                ]
                excluded_list.extend(file_words)
        except Exception as exc:
            print(f"Error: Failed to read excluded words file '{excluded_file}': {exc}")

    return excluded_list


def main() -> None:
    """
    Entry point for the CLI interface.

    Parses arguments, runs the analysis, and writes output.
    """
    args = parse_args()

    excluded_words = load_excluded_words(args.exclude, args.exclude_file)

    # Prepare frequency settings
    min_f: Optional[int] = None
    max_f: Optional[int] = None
    exact_f: Optional[List[int]] = None

    if args.freq_range:
        min_f, max_f = args.freq_range[0], args.freq_range[1]
    elif args.exact_freq:
        exact_f = args.exact_freq

    # Start analysis
    log_progress("Word analysis engine started.")

    total_count, final_frequency = calculate_word_frequency_and_filter(
        input_path=args.input,
        excluded_words=excluded_words,
        target_lang_codes=[lang.lower() for lang in args.lang],
        min_freq=min_f,
        max_freq=max_f,
        exact_freqs=exact_f,
        max_workers_cpu=os.cpu_count() or 4,
    )

    if total_count > 0 and final_frequency:
        write_output(
            frequency_dict=final_frequency,
            total_count=total_count,
            output_format=args.output_format,
            filename=args.filename,
        )
    else:
        print("\nAnalysis complete, but no results matched the specified filters.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nCritical Error: An unexpected error occurred during analysis: {exc}")
