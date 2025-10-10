import csv
import json
import logging
import os
import requests
from bs4 import BeautifulSoup

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


def get_ci_value(d: dict, key: str):
    """Return dict value by key, case-insensitive. Returns '' if not found."""
    if not d:
        return ""
    key_lower = key.lower()
    for k, v in d.items():
        if k and k.lower() == key_lower:
            return v or ""
    return ""


def get_last_processed_info(output_csv):
    if not os.path.exists(output_csv):
        return None, None

    last_row = None
    try:
        with open(output_csv, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                last_row = row
    except Exception as e:
        logging.error(f"Failed reading {output_csv}: {e}")
        return None, None

    if not last_row:
        return None, None

    title = get_ci_value(last_row, "title").strip()
    author = get_ci_value(last_row, "author").strip()
    if not title and not author:
        return None, None
    return title or None, author or None


def find_resume_index_rows(rows, last_title, last_author):
    if not last_title and not last_author:
        return 0

    last_title_norm = (last_title or "").strip().lower()
    last_author_norm = (last_author or "").strip().lower()

    matched_index = None
    for i, row in enumerate(rows):
        title = get_ci_value(row, "title").strip().lower()
        author = get_ci_value(row, "author").strip().lower()
        if title == last_title_norm and author == last_author_norm:
            matched_index = i  # keep last occurrence

    if matched_index is None:
        logging.warning(
            "Last processed (title/author) not found in index.csv — starting from top."
        )
        return 0
    return matched_index + 1


def fetch_book_text(url, max_chars=10000):
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        return text[:max_chars]
    except Exception as e:
        logging.error(f"Error fetching {url}: {e}")
        return ""


def generate_book_summary(book_text, title, author):
    if not book_text.strip():
        return ""

    prompt = f"""
You are a librarian creating book descriptions.

Write a concise, engaging description (4-6 sentences) of this book
that helps a reader browsing a library understand what it is about.
Tone: informative but inviting.
Do NOT add title and author name when generating the description.

Title: {title}
Author(s): {author}

Here are some bits of the book:
{book_text}
"""
    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={"model": MODEL_NAME, "prompt": prompt},
            stream=True,
            timeout=1000,
        )
        response.raise_for_status()

        summary_parts = []
        for line in response.iter_lines():
            if not line:
                continue
            try:
                obj = json.loads(line.decode("utf-8"))
                if "response" in obj:
                    summary_parts.append(obj["response"])
                if obj.get("done", False):
                    break
            except json.JSONDecodeError:
                continue

        return "".join(summary_parts).strip()
    except Exception as e:
        logging.error(f"Error generating summary: {e}")
        return ""


def process_csv(input_csv, output_csv):
    if not os.path.exists(input_csv):
        logging.error(f"Input file not found: {input_csv}")
        return

    with open(input_csv, "r", encoding="utf-8", newline="") as inf:
        reader = list(csv.DictReader(inf))
        if not reader:
            logging.error("Input CSV is empty.")
            return
        input_fieldnames = list(reader[0].keys())

    last_title, last_author = get_last_processed_info(output_csv)
    if last_title or last_author:
        logging.info(
            f"Resuming after last processed: Title='{last_title}' Author='{last_author}'"
        )
    else:
        logging.info("No previous processed row found — starting from top.")

    start_index = find_resume_index_rows(reader, last_title, last_author)
    total = len(reader)

    lc = {c.lower() for c in input_fieldnames}
    writer_fieldnames = list(input_fieldnames)
    if "summary" not in lc:
        writer_fieldnames.append("summary")
    else:
        pass

    write_header = not os.path.exists(output_csv) or os.path.getsize(output_csv) == 0
    with open(output_csv, "a", encoding="utf-8", newline="") as outf:
        writer = csv.DictWriter(outf, fieldnames=writer_fieldnames)
        if write_header:
            writer.writeheader()

        for idx in range(start_index, total):
            row = reader[idx]
            title = get_ci_value(row, "title")
            author = get_ci_value(row, "author")
            url = row.get("remote_url", "") or ""
            logging.info(
                f"Processing input row {idx + 1}/{total}: '{title}' by '{author}'"
            )

            summary = ""
            if url and url.strip().lower().startswith("http"):
                book_text = fetch_book_text(url)
                logging.info(f"Extracted {len(book_text)} characters from {url}")
                summary = generate_book_summary(book_text, title, author)
                logging.info(f"Generated (preview): {summary[:120]}...\n")
            else:
                logging.info("No valid remote_url found; skipping fetch/generation.")

            out_row = dict(row)
            summary_col_name = None
            for fn in writer_fieldnames:
                if fn.lower() == "summary":
                    summary_col_name = fn
                    break
            if not summary_col_name:
                summary_col_name = "summary"
                if summary_col_name not in writer_fieldnames:
                    writer_fieldnames.append(summary_col_name)

            out_row[summary_col_name] = summary
            writer.writerow(out_row)

    logging.info(f"Finished. Output appended to {output_csv}")


if __name__ == "__main__":
    INPUT_CSV = "index.csv"
    OUTPUT_CSV = "index_with_summary.csv"
    process_csv(INPUT_CSV, OUTPUT_CSV)
