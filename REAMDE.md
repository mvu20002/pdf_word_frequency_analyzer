# PDF Word Frequency Analyzer

A high-performance, parallelized word frequency analyzer for processing single PDF files or entire directories of PDFs.
Designed for speed and scalability using multithreading (I/O) + multiprocessing (CPU).

---

## 🚀 Features

* Analyze a **single PDF** or an **entire folder**
* Fast **multithreaded PDF reading**
* Fast **multiprocessing word filtering**
* Optional **language filtering** (ISO 639-1, e.g. `en`, `tr`)
* Exclude words manually or via file
* Frequency filters:
    * Min/Max frequency range
    * Exact frequency values
* Export results in:
    * **TXT**
    * **CSV**
    * **JSON**
* Clean and modular codebase (`reader.py`, `processor.py`, `filters.py`, `cli.py`)

---

## 📦 Installation

```bash
git clone https://github.com/mvu20002/pdf_word_frequency_analyzer.git
pip install -r requirements.txt
```

## 🔧 Basic Usage

Analyze a directory containing PDF files:

```bash
python -m analyzer.cli ./pdfs
```

Analyze a single PDF:

```bash
python -m analyzer.cli ./documents/report.pdf
```

Default output is a .txt file named: `word_analysis_output.txt`

---

## 🧹 Excluding Words

Exclude words directly on the command line:

```bash
python -m analyzer.cli ./pdfs -e the and is of to
```

Exclude using a file (excluded.txt, one word per line):

```bash
python -m analyzer.cli ./pdfs -ef excluded.txt
```

Combine both:

```bash
python -m analyzer.cli ./pdfs -e the and -ef excluded.txt
```

---

## 📊 Frequency Filtering

Filter by frequency range (inclusive):

```bash
python -m analyzer.cli ./pdfs -r 5 10
```

This keeps only words appearing between 5 and 10 times.

Filter by exact frequencies:

```bash
python -m analyzer.cli ./pdfs -ex 3 7 15
```

This keeps only words that appear exactly 3, 7, or 15 times.

---

## 🌍 Language Filtering

Filter words by detected language (ISO 639-1):

```bash
python -m analyzer.cli ./pdfs -l en
```

Multiple languages:

```bash
python -m analyzer.cli ./pdfs -l en tr de
```

If not provided, no language filtering is applied.

---

## 📝 Output Formats

**TXT (default):**

```bash
python -m analyzer.cli ./pdfs -o txt -fn results.txt
```

**CSV:**

```bash
python -m analyzer.cli ./pdfs -o csv -fn frequencies.csv
```

**JSON:**

```bash
python -m analyzer.cli ./pdfs -o json -fn output.json
```

---

## 🧪 Example Commands

Analyze PDFs, exclude common words, keep only English, output JSON:

```bash
python -m analyzer.cli ./pdfs \
    -e the a an is are was were \
    -l en \
    -o json \
    -fn english_filtered.json
```

Full example with exact frequencies & exclusion file:

```bash
python -m analyzer.cli ./reports \
    -ef stopwords.txt \
    -ex 2 4 8 \
    -o csv \
    -fn freq_output.csv
```

---

## 📚 Programmatic Usage

You can import and use the analyzer as a Python module:

```python
from analyzer.processor import calculate_word_frequency_and_filter, write_output

total_count, freq = calculate_word_frequency_and_filter(
    input_path="./docs",
    excluded_words=["the", "and"],
    target_lang_codes=["en"],
    min_freq=3,
    max_freq=20,
)

write_output(freq, total_count, output_format="json", filename="report.json")
```

---

## 🗂 Project Structure

```
your-repo/
├── README.md
├── requirements.txt
├── __init__.py
└── analyzer/
    ├── __init__.py
    ├── reader.py
    ├── processor.py
    ├── filters.py
    └── cli.py
```

---

## 📄 License

MIT License.

---

## 🤝 Contributions

Feel free to submit issues or pull requests!

Happy analyzing! 📘🔍
