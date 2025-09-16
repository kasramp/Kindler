import re
import csv

input_file = "gutindex_aus.txt"
output_file = "gutindex_aus_clean.csv"

date_pattern = re.compile(r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{4}")
entry_pattern = re.compile(
    r"^(?:[A-Za-z]{3} \d{4})\s+(.+?),\s*(.+?)?\[[^\]]+\]\s*\d+A$"
)
author_pattern = re.compile(r"\[Author:\s*(.+?)\]")
title_pattern = re.compile(r"\[Title:\s*(.+?)\]")

rows = []
current_entry = {}
url_columns = ["url_html", "url_text", "url_zip", "url_pdf"]


def assign_url(entry, url):
    url = url.strip()  # remove leading/trailing spaces
    url = re.split(r"\s|\]", url)[0]  # take only the part before first space or ]
    url_lower = url.lower()
    if url_lower.endswith(".html"):
        entry.setdefault("url_html", []).append(url)
    elif url_lower.endswith(".txt"):
        entry.setdefault("url_text", []).append(url)
    elif url_lower.endswith(".zip"):
        entry.setdefault("url_zip", []).append(url)
    elif url_lower.endswith(".pdf"):
        entry.setdefault("url_pdf", []).append(url)
    else:
        entry.setdefault("url_other", []).append(url)


with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        author_match = author_pattern.match(line)
        title_match = title_pattern.match(line)
        if author_match:
            current_entry.setdefault("full_author", []).append(author_match.group(1))
            continue
        if title_match:
            current_entry.setdefault("full_title", []).append(title_match.group(1))
            continue
        entry_match = entry_pattern.match(line)
        if entry_match:
            if current_entry:
                for col in [
                    "full_author",
                    "full_title",
                    "url_html",
                    "url_text",
                    "url_zip",
                    "url_pdf",
                    "url_other",
                ]:
                    if col in current_entry:
                        current_entry[col] = " | ".join(current_entry[col])
                rows.append(current_entry)
                current_entry = {}
            title, author = entry_match.groups()
            title = title.strip().strip('"').strip()
            author = (author or "").strip().removeprefix("by ").strip("'").strip()
            current_entry = {"title": title, "author": author}
            continue
        if line.startswith("http"):
            assign_url(current_entry, line)
            continue

if current_entry:
    for col in [
        "full_author",
        "full_title",
        "url_html",
        "url_text",
        "url_zip",
        "url_pdf",
        "url_other",
    ]:
        if col in current_entry:
            current_entry[col] = " | ".join(current_entry[col])
    rows.append(current_entry)

fieldnames = [
    "title",
    "author",
    "full_author",
    "full_title",
    "url_html",
    "url_text",
    "url_zip",
    "url_pdf",
    "url_other",
]
with open(output_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row.get(k, "") for k in fieldnames})

print(f"Saved {len(rows)} entries to {output_file}")
