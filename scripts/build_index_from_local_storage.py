import os
import sys
import csv
import re
from bs4 import BeautifulSoup, Tag

AUTHOR_RE = re.compile(r"author:\s*(.+)", re.IGNORECASE)
TITLE_RE = re.compile(r"title:\s*(.+)", re.IGNORECASE)
BY_RE = re.compile(r"\bby\b", re.IGNORECASE)
HEADING_TAGS = ["h1", "h2", "h3", "h4"]
BASE_URL = "http://gutenberg.net.au/"


def extract_author_title(html_path):
    author, title = None, None

    try:
        with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
            soup = BeautifulSoup(f, "html.parser")

        # Step 1: Try "Author:" / "Title:" regex first
        for text in soup.stripped_strings:
            if author is None:
                m = AUTHOR_RE.search(text)
                if m:
                    author = m.group(1).strip()
            if title is None:
                m = TITLE_RE.search(text)
                if m:
                    title = m.group(1).strip()
            if author and title:
                return author, title

        # Step 2: Look for first "by" anywhere
        all_tags = [el for el in soup.descendants if isinstance(el, Tag)]
        for i, tag in enumerate(all_tags):
            text = tag.get_text(strip=True)
            if text and BY_RE.search(text):
                # --- scan backward for previous heading ---
                prev_heading = None
                for prev in reversed(all_tags[:i]):
                    if prev.name in HEADING_TAGS and prev.get_text(strip=True):
                        prev_heading = prev.get_text(strip=True)
                        break
                    elif prev.name in ["p", "br"] and not prev.get_text(strip=True):
                        continue
                    elif not prev.get_text(strip=True):
                        continue
                    else:
                        break

                # --- scan forward for next heading ---
                next_heading = None
                for nxt in all_tags[i + 1 :]:
                    if nxt.name in HEADING_TAGS and nxt.get_text(strip=True):
                        next_heading = nxt.get_text(strip=True)
                        break
                    elif nxt.name in ["p", "br"] and not nxt.get_text(strip=True):
                        continue
                    elif not nxt.get_text(strip=True):
                        continue
                    else:
                        break

                if prev_heading and next_heading:
                    title = prev_heading
                    author = next_heading
                    break

    except Exception as e:
        print(f"Error parsing {html_path}: {e}")

    return author, title


def main(input_file, output_file="output.csv"):
    base_path = os.path.dirname(os.path.abspath(input_file))
    with open(input_file, "r", encoding="utf-8") as f:
        html_files = [line.strip() for line in f if line.strip()]

    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            ["author", "title", "location", "relative_location", "remote_url"]
        )

        for html_path in html_files:
            relative_location = os.path.relpath(html_path, base_path)
            remote_url = BASE_URL + relative_location
            author, title = extract_author_title(html_path)
            writer.writerow(
                [author or "", title or "", html_path, relative_location, remote_url]
            )


if __name__ == "__main__":
    # if len(sys.argv) < 2:
    #     print("Usage: python extract_meta.py <file_with_html_paths> [output.csv]")
    #     sys.exit(1)
    #
    # input_file = "/Users/user/gut-au/out.txt"
    # output_file = sys.argv[2] if len(sys.argv) > 2 else "output.csv"
    input_file = "/Users/user/gut-au/out.txt"
    output_file = "index.csv"
    main(input_file, output_file)
