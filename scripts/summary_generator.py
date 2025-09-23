import csv
import json
import logging

import requests
from bs4 import BeautifulSoup

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral"


def fetch_book_text(url, max_chars=10000):
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        return text[:max_chars]
    except Exception as e:
        logging.info(f"Error fetching {url}: {e}")
        return ""


def generate_book_summary(book_text, title, author):
    if not book_text.strip():
        return ""

    prompt = f"""
    You are a librarian creating book descriptions.\n
    Write a concise, engaging description (4-6 sentences) of this book
    that helps a reader browsing a library understand what it is about.\n
    Tone: informative but inviting.\n
    Do NOT add title and author name when generating the description.\n
    Title: {title}\n
    Author(s): {author}.\n This some bits of the book:\n 
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
            if line:
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
        logging.info(f"Error generating summary: {e}")
        return ""


def process_csv(input_csv, output_csv):
    with open(input_csv, "r", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames + ["summary"]

        with open(output_csv, "w", encoding="utf-8", newline="") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                url = row.get("remote_url", "")
                summary = ""

                if url.startswith("http"):
                    logging.info(
                        f"Processing: {row.get('title', 'Unknown')} by {row.get('author', 'Unknown')}"
                    )
                    book_text = fetch_book_text(url)
                    logging.info(f"Extracted {len(book_text)} characters")
                    summary = generate_book_summary(
                        book_text, row.get("title"), row.get("author")
                    )
                    logging.info(f"Summary: {summary[:120]}...\n")

                row["summary"] = summary
                writer.writerow(row)

    logging.info(f"Finished. Output saved to {output_csv}")


if __name__ == "__main__":
    INPUT_CSV = "index.csv"
    OUTPUT_CSV = "index_with_summary.csv"
    process_csv(INPUT_CSV, OUTPUT_CSV)
